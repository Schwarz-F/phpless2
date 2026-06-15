// 1. CRT-Modus sofort beim Laden prüfen (verhindert weißes Aufblitzen)
if (localStorage.getItem('crt-mode') === '1') {
  document.documentElement.classList.add('crt');
}

// 2. Text des Buttons updaten ([ crt: on ] oder [ crt: off ])
function syncCrtLabel() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  document.getElementById('theme-toggle').style.fontSize = "12px";
  document.documentElement.classList.contains('crt')
  ?   document.getElementById('theme-toggle').style.color = 'var(--teal)'
  : document.getElementById('theme-toggle').style.color = '#fff'; // Optional: Stil anpassen

}

// 3. Globaler Click-Listener (Event Delegation für dynamische Buttons)
document.addEventListener('click', function (e) {
  const btn = e.target.closest('#theme-toggle');
  if (!btn) return;
  
  const on = document.documentElement.classList.toggle('crt');
  localStorage.setItem('crt-mode', on ? '1' : '0');
  syncCrtLabel();
});

// 4. Universelle Funktion zum Anhängen des Footers
function appendFooter() {
  const app = document.getElementById('app');
  if (!app || document.getElementById('theme-toggle')) return; // Falls schon da, abbrechen

  const footerHTML = `<footer>idk what to write here · ${new Date().getFullYear()} · <button id="theme-toggle" class="crt-toggle" type="button">crt</button></footer>`;
  app.insertAdjacentHTML('beforeend', footerHTML);

  syncCrtLabel();
}

// Höre auf das Event von index.js oder music.js
document.addEventListener('app-rendered', appendFooter);
document.addEventListener('DOMContentLoaded', syncCrtLabel);