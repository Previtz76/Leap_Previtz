const $ = (id) => document.getElementById(id);
let allEntries = [];
const esc = (s='') => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function badge(label, cls=''){ return `<span class="badge ${cls}">${esc(label)}</span>`; }
function classifyTopic(e){
  const t=((e.title_it||'')+' '+(e.body_it||'')).toLowerCase();
  if(/carplay|android auto|infotainment|spotify|audio|volume|radio|display|schermo|suono/.test(t)) return 'infotainment';
  if(/problema|errore|bug|correzion|difett|non funziona|guasto|patch|risolto/.test(t)) return 'bugs';
  return 'features';
}
function statusLabel(e){ return e.status==='official'?'Fonte ufficiale':e.status==='rumor'?'Rumor / non confermato':'Community / stampa'; }
function render(){
  const q=$('search').value.trim().toLowerCase(), model=$('model').value, status=$('status').value, topic=$('topic').value;
  const list=allEntries.filter(e=>{
    const hay=[e.title_it,e.body_it,e.title_de,e.body_de,e.version,e.market].join(' ').toLowerCase();
    return (!q||hay.includes(q)) && (model==='all'||e.model===model|| (model==='both'&&e.model==='both')) && (status==='all'||e.status===status) && (topic==='all'||classifyTopic(e)===topic);
  });
  $('results').textContent=`${list.length} di ${allEntries.length} voci`;
  $('entries').innerHTML=list.length?list.map(e=>{
    const sourceLinks=(e.sources||[]).map(s=>`<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.label||'Fonte originale')} ↗</a>`).join('');
    const original=(e.body_de||'').trim();
    return `<article class="entry">
      <div class="entry-top"><div><h2>${esc(e.title_it||e.title_de||'Aggiornamento OTA')}</h2><div class="badges">${badge(statusLabel(e),e.status)}${badge(e.model==='both'?'BEV + REEV':e.model)}${e.version?badge('LeapOS '+e.version):''}${e.changed?badge('Nuova / modificata','changed'):''}${e.market?badge(e.market):''}</div></div><time class="entry-date">${esc(e.date||'Data non indicata')}</time></div>
      <p class="summary">${esc(e.summary_it||'')}</p>
      <p>${esc(e.body_it||'Traduzione non disponibile. Consulta il testo originale.')}</p>
      ${sourceLinks?`<div class="source-links">${sourceLinks}</div>`:''}
      ${original?`<details><summary>Mostra testo tedesco originale</summary><div class="original">${esc(original)}</div></details>`:''}
    </article>`;
  }).join(''):'<div class="empty">Nessuna voce corrisponde ai filtri selezionati.</div>';
}
async function init(){
  try{
    const r=await fetch('data/ota.json',{cache:'no-store'}); if(!r.ok) throw new Error('Archivio non disponibile');
    const data=await r.json(); allEntries=data.entries||[];
    $('updated').textContent='Ultimo controllo automatico: '+(data.checked_at||'non disponibile');
    $('count').textContent=allEntries.length;
    $('bev').textContent=data.latest_versions?.BEV||'—';
    $('reev').textContent=data.latest_versions?.REEV||'—';
    ['search','model','status','topic'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',render));
    $('reset').addEventListener('click',()=>{$('search').value='';$('model').value='all';$('status').value='all';$('topic').value='all';render();});
    render();
  }catch(err){$('updated').textContent='Archivio non ancora generato';$('entries').innerHTML='<div class="empty error">Non riesco a caricare l’archivio. Completa il primo aggiornamento GitHub Actions oppure consulta la fonte originale.</div>';}
}
init();
