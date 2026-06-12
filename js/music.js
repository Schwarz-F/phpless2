const CACHE={
get(k){try{return JSON.parse(localStorage.getItem('fos_cache_'+k));}catch{return null;}},
set(k,v){try{localStorage.setItem('fos_cache_'+k,JSON.stringify(v));}catch{}}
};

const esc=s=>(s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

// Die Thumbnails nutzen wir weiterhin, falls das Python-Skript mal keins liefert
const thumb = id => `https://i.ytimg.com/vi/${id}/mqdefault.jpg`;

let CFG={};

async function loadConfig() {
  let cfg = {};
  let ocfg = {};
  try {
    const r = await fetch('./data/config/music.json', { cache: 'no-cache' });
    if (r.ok) cfg = await r.json();
  } catch (e) {
    console.error('music.json nicht ladbar:', e);
  }
  try {
    const r = await fetch('./data/config/config.json', { cache: 'no-cache' });
    if (r.ok) ocfg = await r.json();
  } catch (e) {
    console.error('config.json nicht ladbar:', e);
  }
  return { ...ocfg, ...cfg };
}

// Holt die Songs direkt aus den von GitHub Actions generierten lokalen JSON-Dateien
async function fetchFeedSongs(playlistId){
  const cacheKey = 'ytfeed_' + playlistId;
  const cached = CACHE.get(cacheKey);
  // Cache bleibt aktiv (1 Stunde), um Traffic auf GitHub Pages zu minimieren
  if (cached && (Date.now() - cached.t) < 3600000) return cached.items;

  // NEU: Direkter lokaler Fetch aus data/music/ statt über den fehlerhaften Proxy
  const r = await fetch(`./data/music/${playlistId}.json`, { cache: 'no-cache' });
  if (!r.ok) throw new Error('Lokale Playlist-Datei fehlt oder Status ' + r.status);

  const localItems = await r.json();
  
  // Mapping anpassen, falls Python-Struktur leicht abweicht (id -> videoId)
  const items = localItems.map(e => ({
    title: e.title || '',
    artist: e.artist || '', // Wird im Python-Skript bei Bedarf befüllt
    videoId: e.id || e.videoId || ''
  })).filter(s => s.title && s.videoId);

  if (!items.length) {
  console.warn('Alle Items rausgefiltert. Roh-Daten:', localItems.slice(0,2));
  throw new Error(`Playlist-Datei ist leer (${localItems.length} Einträge, aber alle ohne id/title)`);
}
  CACHE.set(cacheKey, { t: Date.now(), items });
  return items;
}

// Kompakte Song-Zeile: kleines Cover, Titel fett, Artist darunter
function songRow(s){
  return `<a class="song-row" href="https://music.youtube.com/watch?v=${esc(s.videoId)}" target="_blank" rel="noopener">
    <span class="song-thumb"><img src="${thumb(esc(s.videoId))}" alt="" loading="lazy"></span>
    <span class="song-meta">
      <span class="song-title">${esc(s.title)}</span>
      ${s.artist ? `<span class="song-artist">${esc(s.artist)}</span>` : ''}
    </span>
  </a>`;
}

// Playlist-Zeile: Cover-Collage (2x2) + Name aus der Config
function playlistRow(p, i){
  return `<div class="pl-item" id="pl-item-${i}">
    <div class="pl-head" data-idx="${i}">
      <span class="pl-cover" id="pl-cover-${i}"><span class="pl-cover-ph">♫</span></span>
      <span class="pl-meta">
        <span class="pl-title">${esc(p.name || 'unbenannt')}</span>
        ${p.note ? `<span class="pl-note">// ${esc(p.note)}</span>` : ''}
      </span>
      <span class="pl-toggle" id="pl-toggle-${i}">[+]</span>
      <a class="pl-open" href="https://music.youtube.com/playlist?list=${esc(p.id)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">öffnen ↗</a>
    </div>
    <div class="pl-body" id="pl-body-${i}" hidden><span class="note">— lädt —</span></div>
  </div>`;
}

// Cover-Collage aus den ersten 4 Songs bauen
async function loadPlaylistCover(p, i){
  try {
    const songs = await fetchFeedSongs(p.id);
    const el = document.getElementById('pl-cover-' + i);
    if (!el || !songs.length) return;
    if (songs.length >= 4) {
      el.innerHTML = songs.slice(0, 4)
        .map(s => `<img src="${thumb(esc(s.videoId))}" alt="" loading="lazy">`).join('');
      el.classList.add('grid4');
    } else {
      el.innerHTML = `<img src="${thumb(esc(songs[0].videoId))}" alt="" loading="lazy">`;
    }
  } catch (e) { /* ♫-Platzhalter bleibt stehen */ }
}

async function togglePlaylist(i){
  const body = document.getElementById('pl-body-' + i);
  const tgl = document.getElementById('pl-toggle-' + i);
  if (!body) return;

  if (!body.hidden) {
    body.hidden = true;
    if (tgl) tgl.textContent = '[+]';
    return;
  }
  body.hidden = false;
  if (tgl) tgl.textContent = '[–]';

  if (body.dataset.loaded) return;
  const p = (CFG.playlists || [])[i];
  if (!p) return;
  try {
    const songs = await fetchFeedSongs(p.id);
    body.innerHTML = `<div class="song-list">${songs.map(songRow).join('')}</div>`;
    body.dataset.loaded = '1';
  } catch (e) {
    console.error('Laden der Playlist-Datei fehlgeschlagen:', e);
    body.innerHTML = '<span class="err">// daten gerade nicht verfügbar</span>';
  }
}

// Activity-Bilder: Discord nutzt teils eigene Assets, teils externe URLs
function actImg(appId, asset){
  if (!asset) return '';
  if (asset.startsWith('mp:external/')) return 'https://media.discordapp.net/' + asset.slice(3);
  return `https://cdn.discordapp.com/app-assets/${appId}/${asset}.png`;
}

async function fetchNowPlaying(){
  const el = document.getElementById('np-box');
  if (!el || !CFG.discordId) {
    if (el) el.innerHTML = '<span class="note">— keine discord id konfiguriert —</span>';
    return;
  }
  try {
    const r = await fetch(`https://api.lanyard.rest/v1/users/${CFG.discordId}`);
    const d = await r.json();
    if (!d.success) throw new Error('lanyard error');

    const sp = d.data.spotify;
    const acts = d.data.activities || [];
    const listening = acts.find(a => a.type === 2 && !sp);
    const game = acts.find(a => a.type === 0);

    if (sp) {
      el.innerHTML = npCard('♫ hört gerade', sp.song, [sp.artist], sp.album_art_url);
    } else if (listening) {
      const img = listening.assets && listening.assets.large_image
        ? actImg(listening.application_id, listening.assets.large_image) : '';
      el.innerHTML = npCard(
        '',
        listening.details || listening.name,
        [listening.state, listening.assets?.large_text],
        img
      );
    } else if (game) {
      const img = game.assets && game.assets.large_image
        ? actImg(game.application_id, game.assets.large_image) : '';
      el.innerHTML = npCard('▶ spielt gerade', game.name, [game.details, game.state], img);
    } else {
      el.innerHTML = '<span class="note">— gerade nix am laufen —</span>';
    }
  } catch (e) {
    console.error('Lanyard fehlgeschlagen:', e);
    el.innerHTML = '<span class="err">// lanyard nicht erreichbar</span>';
  }
  setTimeout(fetchNowPlaying, 30000);
}

function npCard(label, title, subs, img){
  return `<div class="np-card">
    ${img ? `<span class="np-thumb"><img src="${esc(img)}" alt=""></span>` : ''}
    <span class="np-meta">
      <span class="np-label">${label}</span>
      <span class="np-title">${esc(title)}</span>
      ${(subs || []).filter(Boolean).map(s => `<span class="np-sub">${esc(s)}</span>`).join('')}
    </span>
  </div>`;
}

async function render(cfg = {}) 
{  CFG = cfg;
  const pls = Array.isArray(cfg.playlists) ? cfg.playlists : [];

  document.getElementById('app').innerHTML = `
    <div class="head">
      <h1>/music<span class="blink">_</span></h1>
      <div class="role">youtube music dump</div>
    </div>

    ${cfg.introText ? `<div class="quote">${esc(cfg.introText)}</div>` : ''}

    <a id="now"></a>
    <div class="h">aktuell am laufen</div>
    <span class="note">// live via discord</span>
    <div id="np-box" style="margin-top:12px"><span class="note">— lädt —</span></div>

    <a id="favs"></a>
    <div class="h">aktuelle lieblingssongs</div>
    <span class="note">// live von youtube gezogen</span>
    <div class="song-list" id="fav-list" style="margin-top:12px"><span class="note">— lädt —</span></div>

    <a id="playlists"></a>
    <div class="h">ausgewählte playlists</div>
    <span class="note">// draufklicken zum aufklappen</span>
    <div style="margin-top:12px" id="pl-list">${pls.map(playlistRow).join('') || '<span class="note">— keine playlists gefunden —</span>'}</div>
  `;

  // Start der Datenabrufe
  fetchNowPlaying();

  // Lieblingssongs laden aus favoritesPlaylistId
  if (cfg.favoritesPlaylistId) {
    try {
      const favSongs = await fetchFeedSongs(cfg.favoritesPlaylistId);
      document.getElementById('fav-list').innerHTML = favSongs.map(songRow).join('');
    } catch (e) {
      console.error('Favoriten konnten nicht geladen werden:', e);
      document.getElementById('fav-list').innerHTML = '<span class="err">// favoriten gerade nicht erreichbar</span>';
    }
  } else {
    document.getElementById('fav-list').innerHTML = '<span class="note">— keine favoriten-playlist konfiguriert —</span>';
  }

  // Cover für Playlists asynchron im Hintergrund generieren
  pls.forEach((p, i) => {
    loadPlaylistCover(p, i);
    // Event Listener fürs Auf- und Zuklappen hinzufügen
    const head = document.querySelector(`#pl-item-${i} .pl-head`);
    if (head) {
      head.addEventListener('click', () => togglePlaylist(i));
    }
  });
}
(async () => {
  const cfg = await loadConfig();
  await render(cfg);
})();
