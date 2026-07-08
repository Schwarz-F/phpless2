if (localStorage.getItem('crt-mode') === '1') {
  document.documentElement.classList.add('crt');
}

function syncCrtLabel() {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  document.getElementById('theme-toggle').style.fontSize = "12px";
  document.documentElement.classList.contains('crt')
  ?   document.getElementById('theme-toggle').style.color = 'var(--teal)'
  : document.getElementById('theme-toggle').style.color = '#fff'; // Optional: Stil anpassen

}

document.addEventListener('click', function (e) {
  const btn = e.target.closest('#theme-toggle');
  if (!btn) return;
  
  const on = document.documentElement.classList.toggle('crt');
  localStorage.setItem('crt-mode', on ? '1' : '0');
  syncCrtLabel();
});

async function appendFooter() {
  var viewcounter = localStorage.getItem('visitor_count') || '0';
  if (!document.location.href.includes('.html')) { {
     viewcounter = await fetch('https://hitscounter.dev/api/hit?url=webv1.fabitx.de').then(res => res.text()).then(text => text.split('/')[10].replace('<', '')).catch(() => '0');
    console.log(`Visitor count: ${viewcounter}`);
    localStorage.setItem('visitor_count', viewcounter);
  }}

  const app = document.getElementById('app');
  if (!app || document.getElementById('theme-toggle')) return; // Falls schon da, abbrechen
  console.log(`Visitor count: ${viewcounter}`);
  const footerHTML = `<footer>idk what to write here · ${new Date().getFullYear()} · <button id="theme-toggle" class="crt-toggle" type="button">crt</button> · Visitor count: ${viewcounter}</footer>`;
  app.insertAdjacentHTML('beforeend', footerHTML);

  syncCrtLabel();
}

document.addEventListener('app-rendered', appendFooter);
document.addEventListener('DOMContentLoaded', syncCrtLabel);