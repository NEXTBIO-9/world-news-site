/* NEXT BIO: client-only display preference. No API calls, no changes to article data. */
(function(){
 'use strict';
 const KEY='nextbio-title-translation';
 let enabled=true;
 try{enabled=localStorage.getItem(KEY)!=='off'}catch(e){}
 window.NBTitleTranslation={
  enabled:()=>enabled,
  title:a=>enabled?(a.title_ko||a.title||'제목 없음'):(a.title||'제목 없음')
 };
 function init(){
  if(document.getElementById('nb-title-translation-toggle'))return;
  const bar=document.createElement('div');
  bar.className='nb-translation-control';
  bar.innerHTML='<label for="nb-title-translation-toggle">🌐 뉴스 제목·기사 요약 번역</label><button type="button" id="nb-title-translation-toggle" aria-pressed="true"></button><span class="nb-translation-hint">번역이 없는 기사는 원문으로 표시됩니다.</span>';
  const target=document.getElementById('nb-intelligence')||document.getElementById('latest-list');
  if(target)target.parentNode.insertBefore(bar,target);
  else document.body.insertBefore(bar,document.body.firstChild);
  const btn=document.getElementById('nb-title-translation-toggle');
  function update(){btn.textContent=enabled?'한국어 ON':'원문 OFF';btn.setAttribute('aria-pressed',String(enabled));}
  btn.addEventListener('click',()=>{
   enabled=!enabled;
   try{localStorage.setItem(KEY,enabled?'on':'off')}catch(e){}
   update();
   if(typeof window.render==='function')window.render();
   document.dispatchEvent(new Event('nb-title-translation-changed'));
  });
  update();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
 else init();
})();
