const DEFAULT_CFG = {};
const DEFAULT_LINKS = [];
const csvData = null;

const CACHE={
  get(k){try{return JSON.parse(localStorage.getItem('fos_cache_'+k));}catch{return null;}},
  set(k,v){try{localStorage.setItem('fos_cache_'+k,JSON.stringify(v));}catch{}}
};

const esc=s=>(s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const aboutClean=s=>(s||'').replace(/<(?!\/?(span|br)\b)[^>]*>/gi,'');

let CFG={};

// ANGEPASST: Direkter Abruf aus data/config/config.json
function parseCSVText(csvText) {
    if (!csvText) return [];
    const lines = csvText.trim().split('\n');
    if (lines.length === 0 || !lines[0]) return [];
    
    const headers = lines[0].split(';').map(h => h.trim());
    
    return lines.slice(1).map(line => {
        const values = line.split(';').map(v => v.trim());
        const obj = {};
        headers.forEach((header, index) => {
            obj[header] = values[index] || '';
        });
        return obj;
    });
}

// 1. Konfiguration UND CSV parallel/nacheinander laden
async function loadConfig() {
    let cfg = { ...DEFAULT_CFG };

    // 1. JSON-Config ODER LocalStorage laden
    try {
        const r = await fetch('./data/config/config.json', { cache: 'no-cache' });
        if (r.ok) {
            const jsonData = await r.json();
            cfg = { ...cfg, ...jsonData };
        } else {
            // Falls Datei nicht da ist, LocalStorage probieren
            const ls = JSON.parse(localStorage.getItem('fos_cfg') || '{}');
            if (Object.keys(ls).length) cfg = { ...cfg, ...ls };
        }
    } catch (e) {
        // Falls Netzwerkfehler, LocalStorage probieren
        try {
            const ls = JSON.parse(localStorage.getItem('fos_cfg') || '{}');
            if (Object.keys(ls).length) cfg = { ...cfg, ...ls };
        } catch (err) {}
    }

    // 2. SEPARAT UND UNABHÄNGIG: CSV-Datei laden
    try {
        const csvResponse = await fetch('./data/config/watchlist.csv');
        if (csvResponse.ok) {
            const csvText = await csvResponse.text();
            cfg.watchlist = parseCSVText(csvText);
        } else {
            console.error("CSV-Datei wurde auf dem Server nicht gefunden (Status:", csvResponse.status, ")");
            cfg.watchlist = [];
        }
    } catch (e) {
        console.error("Netzwerkfehler beim Laden der CSV:", e);
        cfg.watchlist = [];
    }

    return cfg;
}

// 2. Synchrones Rendern (Nutzt die Daten, die jetzt in cfg.watchlist liegen)
function render(cfg) {
    CFG = cfg;
    const links = Array.isArray(cfg.links) && cfg.links.length ? cfg.links : DEFAULT_LINKS;
    const np = (cfg.operatorName || '').trim().split(' ');
    const ini = (np[0] || '?').substring(0, 2).toUpperCase();
    
    const linksH = links.map(l =>
        `<div class="row"><span class="b"></span>` +
        `<span>${esc(l.title)}:</span>` +
        `<a href="${esc(l.url)}" target="_blank" rel="noopener">${l.sub ? esc(l.sub) : esc(l.url)}</a></div>`
    ).join('');

    // Da cfg.watchlist nun ein fertiges Array ist, funktioniert dein Original wieder perfekt!
    const wlH = (cfg.watchlist || []).map(w =>
        `<li><span class="dot s-${esc(w.status)}"></span><a id="wl-link" href="https://www.imdb.com/de/title/${esc(w.imdb)}" target="_blank" rel="noopener">${esc(w.title)}</a>` +
        `<span class="tag">${esc(w.type)}</span><span class="tag">${esc(w.ep || '')}</span></li>`
    ).join('');
  const avInner = cfg.profilePicture
    ? `<img id="me-img" src="${esc(cfg.profilePicture)}" alt="">`
    : `<span id="me-ini">${ini}</span>`;

  document.getElementById('app').innerHTML=`
    <div class="head">
      <h1>hi, i'm ${esc(np[0])}<span class="blink">_</span></h1>
      <div class="role">${esc(cfg.operatorRole||'')}</div>
    </div>

    <a id="about"></a>
    <div class="h">About Me</div>
    <span class="note">// i'm a note</span>
    <div class="me">
      <div class="me-pic" id="me-pic">
        ${avInner}
        <span class="sdot offline" id="dc-sdot"></span>
      </div>
      <div>
        <a class="dc-line" href="${esc(cfg.discordUrl||'#')}" target="_blank" rel="noopener" style="text-decoration:none">
          <span class="dc-uname" id="dc-uname">${esc(cfg.discordName||'---')}</span>
          <span style="color:var(--line)">•</span>
          <span class="dc-stxt offline" id="dc-stxt">Offline</span>
        </a>
        <div>${aboutClean(cfg.aboutHtml)}</div>
      </div>
    </div>

    <a id="links"></a>
    <div class="h">where to find me</div>
    <span class="secret-note">// if you can read this, you've discovered a secret :)</span>
    <div><ul>${linksH}</ul></div>

    <a id="watch"></a>
    <div class="h">currently watching</div>
    <span class="note">// please judge</span>
    <div style="margin-top:10px"><ul class="wl">${wlH||'<li class="note">— nix —</li>'}</ul></div>

    <a id="badges"></a>
    <div class="h">Badges</div>
    <span class="note">// 88 × 31 px of sth. </span>
    <div style="margin-top:10px"><div class="wb-wall" id="wb-wall"><span class="note">— lädt —</span></div></div>

    <footer>idk what to write here · ${new Date().getFullYear()}</footer>
  `;
}

const ST_TEXT={online:'Online',idle:'Abwesend',dnd:'Nicht stören',offline:'Offline'};

function applyDiscordStatus(status,username,avatarUrl){
  const dot=document.getElementById('dc-sdot');
  if(dot)dot.className='sdot '+status;
  const st=document.getElementById('dc-stxt');
  if(st){st.className='dc-stxt '+status;st.textContent=ST_TEXT[status]||'Offline';}
  if(username){const u=document.getElementById('dc-uname');if(u)u.textContent=username;}
  if(avatarUrl && !CFG.profilePicture){
    const pic=document.getElementById('me-pic');
    const img=document.getElementById('me-img');
    if(img){img.src=avatarUrl;}
    else if(pic){
      const ini=pic.querySelector('#me-ini');if(ini)ini.remove();
      const newImg=document.createElement('img');
      newImg.id='me-img';newImg.alt='';newImg.src=avatarUrl;
      pic.insertBefore(newImg,pic.firstChild);
    }
  }
  CACHE.set('dc',{status,username,avatarUrl});
}

async function fetchDiscord(){
  const dc=CACHE.get('dc');
  if(dc)applyDiscordStatus(dc.status,dc.username,dc.avatarUrl);
  if(!CFG.discordId){applyDiscordStatus('offline',CFG.discordName,null);return;}
  try{
    const r=await fetch(`https://api.lanyard.rest/v1/users/${CFG.discordId}`);
    const d=await r.json();
    if(d.success){
      const u=d.data.discord_user;
      const status=d.data.discord_status||'offline';
      const av=u.avatar?`https://cdn.discordapp.com/avatars/${u.id}/${u.avatar}.png?size=128`:null;
      applyDiscordStatus(status,u.username,av);
      setTimeout(fetchDiscord,30000);
    }
  }catch{
    if(!dc)applyDiscordStatus('offline',CFG.discordName,null);
  }
}

// ANGEPASST: Direkter Abruf aus data/config/badges.json
async function loadBadges(){
  let list=[];
  try{
    const r=await fetch('./data/config/badges.json',{cache:'no-cache'});
    if(r.ok)list=await r.json();
  }catch(e){}
  const wall=document.getElementById('wb-wall');
  if(!wall)return;
  wall.innerHTML = Array.isArray(list)&&list.length
    ? list.map(b=>`<a href="${esc(b.url)}" target="_blank" rel="noopener" class="wb"><img src="${esc(b.img)}" alt="${esc(b.alt||'')}" width="88" height="31" loading="lazy"></a>`).join('')
    : '<span class="note">— noch keine —</span>';
}

loadConfig().then(render).then(fetchDiscord).then(loadBadges).catch(e=>{
  document.getElementById('app').innerHTML='<span class="err">// hoppla, config kaputt</span>';
  console.error(e);
});