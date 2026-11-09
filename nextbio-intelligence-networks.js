/* NEXT BIO: official WHO notices + bookmarks, translation toggle integration. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const style=document.createElement('style');style.textContent=`
#nb-bookmark-open{display:none!important}
#nb-intelligence .nbm-tabs{display:flex;gap:18px;margin:0 0 9px;border-bottom:1px solid #324760;flex-shrink:0}
#nb-intelligence .nbm-tabs button{appearance:none;border:0;border-bottom:2px solid transparent;border-radius:0;background:transparent;color:#91a9c4;font-size:13px;font-weight:650;padding:8px 2px 10px;cursor:pointer;box-shadow:none}
#nb-intelligence .nbm-tabs button[aria-selected=true]{color:#f0f8ff;border-bottom-color:#48cbbb}
#nb-intelligence .nbm-tabs button:hover{color:#fff}
#nb-intelligence .nbm-alerts-panel>h3{display:none}
#nb-intelligence .nbm-alerts-panel>#nb-alerts{flex:1;min-height:0;overflow-y:auto}
#nb-intelligence .nbm-alerts-panel>#nb-bookmarks{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;margin:0;padding:0;border:0;background:transparent;max-height:none;height:auto}
#nb-intelligence .nbm-alerts-panel>#nb-bookmarks[hidden],#nb-intelligence .nbm-alerts-panel>#nb-alerts[hidden]{display:none!important}
#nb-intelligence .nbm-alerts-panel>#nb-bookmarks>h3{display:none}
#nb-intelligence .nbm-alerts-panel #nb-saved-list{flex:1;min-height:0;overflow-y:auto;max-height:none;grid-template-columns:minmax(0,1fr)}
#nb-intelligence .nbm-alerts-panel .nb-scrap-toolbar{min-width:0;flex-shrink:0}
#nb-intelligence .nbm-alerts-panel .nb-scrap-toolbar>*{max-width:100%}
#nb-intelligence .nbm-official{height:310px;max-height:310px;min-height:0;display:flex;flex-direction:column;overflow:hidden;padding:12px 14px;border:1px solid var(--border,#334155);border-radius:7px;box-sizing:border-box}
#nb-intelligence .nbm-official h3{margin:0 0 6px;font-size:14px}
#nb-intelligence .nbm-official .nbm-meta{font-size:11px;color:#91a9c4;margin-bottom:8px}
#nb-intelligence .nbm-official .nbm-list{flex:1;min-height:0;overflow-y:auto;scrollbar-width:thin}
#nb-intelligence .nbm-official .nbm-item{padding:10px 0;border-top:1px solid #324760;font-size:12px;line-height:1.55}
#nb-intelligence .nbm-official .nbm-item a{color:#d9efff;text-decoration:none;font-weight:650}
#nb-intelligence .nbm-official .nbm-item a:hover{text-decoration:underline}
#nb-intelligence .nbm-official .nbm-source{display:block;margin-top:4px;color:#9db5ca;font-size:11px}
#nb-intelligence .nbm-official .nbm-empty{padding:20px 2px;color:#aabed0;font-size:12px;line-height:1.7}
@media(max-width:780px){#nb-intelligence .nb2-columns{grid-template-columns:minmax(0,1fr)!important}}
`;document.head.append(style);
const node=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e};
let officialItems=[],officialUpdated=null,officialList=null,officialMeta=null;
function translatedTitle(a){
 const enabled=window.NBTitleTranslation?.enabled?.()??true;
 return enabled?String(a.title_ko||a.title||'제목 없음'):String(a.title||'제목 없음');
}
function renderOfficial(){if(!officialList)return;officialList.replaceChildren();
 if(!officialItems.length){officialList.append(node('p','nbm-empty','현재 수집된 공식 감염병 발표가 없습니다. 공식 수집 작업을 확인해 주세요.'));return;}
 for(const a of officialItems.slice(0,30)){
  const item=node('div','nbm-item');let link=null;
  try{const url=new URL(String(a.url));if(url.protocol==='https:'||url.protocol==='http:'){link=node('a','',translatedTitle(a));link.href=url.href;link.target='_blank';link.rel='noopener noreferrer'}}catch{}
  item.append(link||node('span','',translatedTitle(a)));
  const d=new Date(a.published||'');const date=Number.isFinite(d.getTime())?d.toLocaleDateString('ko-KR'):'날짜 미상';
  item.append(node('span','nbm-source',String(a.source||'WHO')+' · '+date));officialList.append(item);
 }
 if(officialUpdated){const d=new Date(officialUpdated);if(Number.isFinite(d.getTime()))officialMeta.textContent='WHO 공식 발표 · 마지막 수집 '+d.toLocaleString('ko-KR');}
}
async function load(){try{const r=await fetch('./data/bio-official.json?v='+Math.floor(Date.now()/300000),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();officialItems=Array.isArray(d.items)?d.items:[];officialUpdated=d.updated||null;renderOfficial()}catch{if(officialList)officialList.replaceChildren(node('p','nbm-empty','공식 발표 데이터를 불러오지 못했습니다.'))}}
function init(){const columns=document.querySelector('#nb-intelligence .nb2-columns'),alerts=$('nb-alerts'),bookmarks=$('nb-bookmarks');if(!columns||!alerts||!bookmarks)return;
 const left=alerts.closest('section');if(!left)return;left.classList.add('nbm-alerts-panel');
 const tabs=node('div','nbm-tabs');tabs.setAttribute('role','tablist');
 const alertBtn=node('button','','⚡ 신규·주요 뉴스'),bookBtn=node('button','','☆ 북마크');
 for(const b of [alertBtn,bookBtn]){b.type='button';b.setAttribute('role','tab')}
 tabs.append(alertBtn,bookBtn);left.insertBefore(tabs,alerts);left.append(bookmarks);
 for(const s of [...columns.children])if(s!==left)s.remove();
 const right=node('section','nbm-official');right.id='nbm-official';right.append(node('h3','','🏥 공식 감염병 발표'));
 officialMeta=node('div','nbm-meta','WHO 공식 발표 · 제목 번역 ON/OFF 연동');right.append(officialMeta);
 officialList=node('div','nbm-list');right.append(officialList);columns.append(right);
 function show(book){alerts.hidden=book;bookmarks.hidden=!book;alertBtn.setAttribute('aria-selected',String(!book));bookBtn.setAttribute('aria-selected',String(book))}
 alertBtn.addEventListener('click',()=>show(false));bookBtn.addEventListener('click',()=>show(true));$('nb-bookmark-open')?.addEventListener('click',()=>show(true),{capture:true});show(false);
 document.addEventListener('nb-title-translation-changed',renderOfficial);load();setInterval(load,300000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
