const esc = s => (s == null ? '' : String(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const DEFAULT_PLACES = [];
const COLORS = { home: '#e08358', visited: '#4fc7ad', want: '#2d44c4' };

let map, markers = {};
let currentOpenPlaceIndex = null;

function initMap() {
  map = L.map('map', { worldCopyJump: true, minZoom: 2 }).setView([45, 15], 3);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: 'abcd',
    maxZoom: 19
  }).addTo(map);

  map.on('popupclose', function () {
    closeGallery();
  });
}

async function loadPlaces() {
  try {
    const r = await fetch('./data/config/travel.json', { cache: 'no-cache' });
    if (r.ok) {
      const d = await r.json();
      if (Array.isArray(d) && d.length) return d;
    }
  } catch (e) {}
  return DEFAULT_PLACES;
}

function render(places) {
  const list = document.getElementById('place-list');

  // Listeneinträge rendern
  list.innerHTML = places.map((p, i) => {
    const dc = p.status || 'visited';
    return `<li class="place" id="place-item-${i}">
      <span class="dot ${dc}"></span>
      <span class="city" style="cursor:pointer; font-weight:bold;" onclick="focusPlace(${i})">${esc(p.city)}</span>
      <span class="meta">${esc(p.country || '')}${p.note ? ' · ' + esc(p.note) : ''}${p.status === 'want' ? ' · (geplant)' : ''}</span>
      <span class="times"style="margin-left: 10px;float:right;">${!p.count ? `${p.dates.length}x` : `${esc(p.count || '')}`}</span>
      <div class="folder-container" style="display:none;"></div>
    </li>`;
  }).join('');

  // Marker auf der Karte setzen
  places.forEach((p, i) => {
    if (typeof p.lat !== 'number' || typeof p.lon !== 'number') return;
    const color = COLORS[p.status] || '#4fc7ad';
    const m = L.circleMarker([p.lat, p.lon], { radius: 7, color: '#000', weight: 1, fillColor: color, fillOpacity: .9 }).addTo(map);

    let popupContent = `<b>${esc(p.city)}</b>${p.country ? ' (' + esc(p.country) + ')' : ''}`;
    if (p.note) popupContent += `<br>${esc(p.note)}`;
    
    // Bedingung erweitert: Zeigt den Hinweis auch an, wenn globale Bilder existieren
    if ((p.dates && p.dates.length > 0) || (p.images && p.images.length > 0)) {
      popupContent += `<br><i>Klick für Infos ${p.images.length > 0 ? "& Fotos" : ""}</i>`;
    }

    m.bindPopup(popupContent);
    m.on('click', () => loadGallery(p, i));

    markers[i] = m;
  });

  const pts = places.filter(p => typeof p.lat === 'number').map(p => [p.lat, p.lon]);
  if (pts.length) map.fitBounds(pts, { padding: [40, 40], maxZoom: 6 });

  window._places = places;
}

function focusPlace(i) {
  const m = markers[i]; if (!m) return;
  if (currentOpenPlaceIndex === i) {
    map.closePopup();
    return;
  }
  map.setView(m.getLatLng(), 7, { animate: true }); m.openPopup();
  loadGallery(window._places[i], i);
}
window.focusPlace = focusPlace;

function closeGallery() {
  if (currentOpenPlaceIndex !== null) {
    const prevLi = document.getElementById(`place-item-${currentOpenPlaceIndex}`);
    if (prevLi) {
      const container = prevLi.querySelector('.folder-container');
      container.innerHTML = '';
      container.style.display = 'none';
    }
  }
  currentOpenPlaceIndex = null;
}

function loadGallery(p, index) {
  const isSame = (currentOpenPlaceIndex === index);
  closeGallery();

  if (isSame) {
    map.closePopup();
    return;
  }

  // Abbrechen, falls weder globale Bilder noch Trips vorhanden sind
  const hasGlobalImages = p.images && p.images.length > 0;
  const hasTrips = p.dates && p.dates.length > 0;
  if (!hasGlobalImages && !hasTrips) {
    return;
  }

  currentOpenPlaceIndex = index;

  const li = document.getElementById(`place-item-${index}`);
  if (!li) return;
  const container = li.querySelector('.folder-container');

  // 1. NEU: Globale Orts-Fotos rendern (ohne festen Trip)
  let globalImagesHtml = '';
  if (hasGlobalImages) {
    globalImagesHtml = `
      <div class="date-item global-media-section" style="margin-bottom: 10px;">
        <div class="list-gallery-grid" id="global-gallery-grid-${index}" style="display: grid; margin-top: 5px;">${
          p.images.map(imgUrl =>
            `<img src="${esc(imgUrl)}" loading="lazy" onclick="event.stopPropagation(); openLightbox('${esc(imgUrl)}')" alt="">`
          ).join('')
        }</div>
      </div>
    `;
  }

  // 2. Vorhandene Reisen/Trips rendern
  let datesHtml = '';
  if (hasTrips) {
    datesHtml = p.dates.map((d, tripIndex) => {
      if (!d.from) return '';

      let text = esc(d.from);
      if (d.to) text += ` bis ${esc(d.to)}`;

      let commentHtml = d.comment ? `<span class="date-comment">- ${esc(d.comment)}</span>` : '';
      const hasImages = d.images && d.images.length > 0;
      let tripImagesHtml = '';
      if (d.images && d.images.length > 0) {
        tripImagesHtml = `<div class="list-gallery-grid" id="gallery-grid-${index}-${tripIndex}" style="display:none;">${
          d.images.map(imgUrl =>
            `<img src="${esc(imgUrl)}" loading="lazy" onclick="event.stopPropagation(); openLightbox('${esc(imgUrl)}')" alt="">`
          ).join('')
        }</div>`;
        text += ` ⏷`;
      }

      return `<div class="date-item">
      <span ${hasImages ? `class="date-header-hover" onclick="event.stopPropagation(); toggleTripGallery('${index}', '${tripIndex}')" ` : 'class="date-header"'}>
        <b>// ${text}</b>${commentHtml}
      </span>
      ${tripImagesHtml}
    </div>`;
  }).join('');
}

  // HTML zusammensetzen und einfügen
  container.innerHTML = `
    <div class="list-gallery-box" onclick="event.stopPropagation();">
      <div class="folder-title">${esc(p.picturecaption || p.city)}</div>
      ${globalImagesHtml}
      ${datesHtml}
    </div>
  `;
  container.style.display = '';
}
window.loadGallery = loadGallery;

function toggleTripGallery(placeIdx, tripIdx) {
  const grid = document.getElementById(`gallery-grid-${placeIdx}-${tripIdx}`);
  if (!grid) return;

  if (grid.style.display === 'none') {
    grid.style.display = 'grid';
  } else {
    grid.style.display = 'none';
  }
}
window.toggleTripGallery = toggleTripGallery;

function openLightbox(url) {
  const lb = document.getElementById('lightbox');
  lb.querySelector('img').src = url; lb.classList.add('open');
}
window.openLightbox = openLightbox;

document.getElementById('lightbox').addEventListener('click', function () { this.classList.remove('open'); });

// Start-Initialisierung
(async () => {
  initMap();
  const places = await loadPlaces();
  document.dispatchEvent(new Event('app-rendered'));
  render(places);
})().catch(e => {
  document.getElementById('place-list').innerHTML = '<li class="err">// fehler beim laden</li>';
  console.error(e);
});
