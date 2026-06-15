/* ── KONFIG: hier eintragen ───────────────── */
const GFORM_ID    = '1FAIpQLScFI5FHVJBKyGxIawUh_1mmQsuf1zj_dyx9joXf3WTa7-EZog';        // aus der Formular-URL
const ENTRY_NAME  = 'entry.725180336';      // Feld-ID: Name
const ENTRY_CAT   = 'entry.1450354384';      // Feld-ID: Kategorie
const ENTRY_TEXT  = 'entry.2013973822';      // Feld-ID: Vorschlag


const $=id=>document.getElementById(id);
const formLoadedAt=Date.now();
let capA=0, capB=0;

function newCaptcha(){
  capA=Math.floor(Math.random()*8)+1;
  capB=Math.floor(Math.random()*8)+1;
  $('cap-label').textContent=`// are you a human? ${capA} + ${capB} = ?`;
  $('sg-captcha').value='';
}
newCaptcha();

function submit(){
  const btn=$('sg-send');
  const name=$('sg-name').value.trim();
  const cat=$('sg-cat').value;
  const text=$('sg-text').value.trim();
  const st=$('sg-status');

  // 1) Honeypot
  if($('sg-website').value){return;}

  // 2) Zeitfalle (zu schnell = Bot)
  if(Date.now()-formLoadedAt < 2500){
    st.className='err';st.textContent='// a moment please…';return;
  }

  // 3) Pflichtfeld
  if(!text){st.className='err';st.textContent='// suggestion cannot be empty';return;}

  // 4) Mini-CAPTCHA
  const capAns=parseInt(($('sg-captcha').value||'').trim(),10);
  if(capAns !== capA+capB){
    st.className='err';st.textContent='// calculation is incorrect';newCaptcha();return;
  }

  // 5) Verstecktes Google-Form bauen & absenden
  btn.disabled=true;
  st.className='note';st.textContent='// sende…';

  const f=document.createElement('form');
  f.action=`https://docs.google.com/forms/d/e/${GFORM_ID}/formResponse`;
  f.method='POST';
  f.target='hidden_iframe';
  const add=(n,v)=>{const i=document.createElement('input');i.type='hidden';i.name=n;i.value=v;f.appendChild(i);};
  add(ENTRY_NAME, name||'anonym');
  add(ENTRY_CAT,  cat);
  add(ENTRY_TEXT, text);
  document.body.appendChild(f);
  f.submit();
  setTimeout(()=>{
    f.remove();
    $('sg-name').value='';$('sg-text').value='';
    newCaptcha();
    btn.disabled=false;
    st.className='ok';st.textContent='// thank you! your suggestion has been submitted';
  }, 800);
}

document.addEventListener('DOMContentLoaded', () => {
  // 1. Prüfen, ob die Elemente überhaupt auf dieser Seite existieren
  if ($('cap-label') && $('sg-captcha')) {
    newCaptcha();
  }

  const sendBtn = $('sg-send');
  if (sendBtn) {
    sendBtn.onclick = submit;
  }

  // 2. ERST WENN ALLES BEREIT IST: Das Signal für den Footer abfeuern
  document.dispatchEvent(new Event('app-rendered'));
});
$('sg-send').onclick=submit;