/* NEXT BIO title translations: cached Korean titles, with original-title fallback. */
(function(){
 'use strict';
 const KEY='nextbio-title-translation';
 let enabled=true;
 let translations={};
 try{enabled=localStorage.getItem(KEY)!=='off'}catch(e){}
 window.NBTitleTranslation={
  enabled:()=>enabled,
  title:a=>enabled?(a.title_ko||translations[a.title]||a.title||'제목 없음'):(a.title||'제목 없음')
 };
 function refresh(){
  if(typeof window.render==='function')window.render();
  document.dispatchEvent(new Event('nb-title-translation-changed'));
  window.dispatchEvent(new Event('nextbio-translation-preference'));
 }
 function init(){
  if(document.getElementById('nb-title-translation-toggle'))return;
  const bar=document.createElement('div');
  bar.className='nb-translation-control';
  bar.innerHTML='<label for="nb-title-translation-toggle">🌐 뉴스 제목 번역</label><button type="button" id="nb-title-translation-toggle" aria-pressed="true"></button><span class="nb-translation-hint">번역되지 않은 제목은 원문으로 표시됩니다.</span>';
  const target=document.getElementById('nb-intelligence')||document.getElementById('latest-list');
  if(target)target.parentNode.insertBefore(bar,target);
  else document.body.insertBefore(bar,document.body.firstChild);
  const btn=document.getElementById('nb-title-translation-toggle');
  function update(){btn.textContent=enabled?'한국어 ON':'원문 OFF';btn.setAttribute('aria-pressed',String(enabled));}
  btn.addEventListener('click',()=>{
   enabled=!enabled;
   try{localStorage.setItem(KEY,enabled?'on':'off')}catch(e){}
   update();refresh();
  });
  update();
  window.addEventListener('storage',e=>{if(e.key===KEY){enabled=e.newValue!=='off';update();refresh();}});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
 else init();
 fetch('./data/title-translations.json?ts='+Math.floor(Date.now()/300000),{cache:'no-store'})
  .then(r=>{if(!r.ok)throw new Error('No translations cache');return r.json();})
  .then(d=>{translations=d.translations||{};refresh();})
  .catch(()=>{});
})();
