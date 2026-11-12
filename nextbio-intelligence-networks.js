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
#nb-intelligence .nbm-official-tabs{display:flex;gap:12px;flex-wrap:wrap;border-bottom:1px solid #324760;margin-bottom:9px;flex-shrink:0}
#nb-intelligence .nbm-official-tabs button{background:transparent;border:0;border-bottom:2px solid transparent;color:#91a9c4;padding:5px 0 9px;cursor:pointer;font-size:12px;font-weight:700}
#nb-intelligence .nbm-official-tabs button[aria-selected=true]{color:#f0f8ff;border-bottom-color:#48cbbb}
#nb-intelligence .nbm-border-panel{flex:1;min-height:0;overflow-y:auto;color:#d9e9fa;font-size:12px;line-height:1.65}
#nb-intelligence #nbm-navy-panel[hidden],#nb-intelligence .nbm-border-panel[hidden],#nb-intelligence .nbm-official .nbm-list[hidden],#nb-intelligence .nbm-official .nbm-meta[hidden]{display:none!important}
#nb-intelligence .nbm-border-panel .nbm-border-status{padding:11px;border:1px solid #3a536e;border-radius:9px;background:#26394f;margin:9px 0}
#nb-intelligence .nbm-border-panel strong{display:block;color:#91c5ff;font-size:18px;margin:4px 0}
#nb-intelligence .nbm-progress-track{height:9px;background:#3b506a;border-radius:99px;overflow:hidden;margin:8px 0}
#nb-intelligence .nbm-progress-fill{height:100%;background:#3195f5;border-radius:99px}
#nb-intelligence .nbm-border-panel a{color:#91c5ff}
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
 // Collapse identical WHO report titles into one latest report, preserving original JSON and translations.
 const byTitle=new Map();
 for(const a of officialItems){
  const key=String(a.title||'').normalize('NFKC').toLocaleLowerCase('en').replace(/\s+/g,' ').replace(/[–—]/g,'-').trim();
  if(!key)continue;
  const previous=byTitle.get(key);
  const date=Date.parse(a.published||'')||0;
  const oldDate=previous?(Date.parse(previous.published||'')||0):-1;
  if(!previous||date>oldDate||(date===oldDate&&!previous.title_ko&&a.title_ko))byTitle.set(key,a);
 }
 const unique=[...byTitle.values()].sort((a,b)=>(Date.parse(b.published||'')||0)-(Date.parse(a.published||'')||0));
 for(const a of unique.slice(0,30)){
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
 const right=node('section','nbm-official');right.id='nbm-official';
 const rightTabs=node('div','nbm-official-tabs');rightTabs.setAttribute('role','tablist');rightTabs.setAttribute('aria-label','공식 발표 및 북한 국경 장벽 현황');
 const whoBtn=node('button','','🏥 공식 감염병 발표'),borderBtn=node('button','','🧱 북한 국경 장벽'),navyBtn=node('button','','⚓ 중국 해군 동향');
 for(const b of [whoBtn,borderBtn,navyBtn]){b.type='button';b.setAttribute('role','tab');rightTabs.append(b)}right.append(rightTabs);
 officialMeta=node('div','nbm-meta','WHO 공식 발표 · 제목 번역 ON/OFF 연동');right.append(officialMeta);
 officialList=node('div','nbm-list');right.append(officialList);
 const borderPanel=node('div','nbm-border-panel');borderPanel.id='nbm-border-panel';borderPanel.setAttribute('role','tabpanel');
 borderPanel.append(node('div','nbm-meta','남북 접경지역 요새화 · 2026년 8월 기준 보도 추정치'));
 const addEstimate=(label,value,pct,note)=>{const wrap=node('div','nbm-border-status');wrap.append(node('span','',label+' · 추정치'));wrap.append(node('strong','',value));const track=node('div','nbm-progress-track');const fill=node('div','nbm-progress-fill');fill.style.width=pct+'%';track.append(fill);wrap.append(track);wrap.append(node('span','',note));borderPanel.append(wrap)};
 addEstimate('지면 정리 작업','약 90%',90,'남부 국경 관련 보도 추정 · 전체 장벽 완공률이 아님');
 addEstimate('철책·지뢰지대 구축','약 30~60%',60,'구간별 추정 범위 · 막대는 상한 60%를 나타냄');
 borderPanel.append(node('p','','※ 남북 접경지역 추정치입니다. 중국·러시아 접경지역 전체 진행률과는 다르며, 공식 확정 수치가 아닙니다.'));
 borderPanel.append(node('p','','2026년 8월 기준 추정치로 보도된 값이며, 이후 공정률을 실시간 반영하지 않습니다.'));
 const checkInfo=node('p','nbm-meta','공개 보도 자동 확인: 매일 1회 · 첫 실행 대기 중');borderPanel.append(checkInfo);
 async function updateBorderCheck(){try{const r=await fetch('./data/nk-border-status.json?ts='+Math.floor(Date.now()/3600000),{cache:'no-store'});if(!r.ok)return;const d=await r.json();if(d.last_checked){const date=new Date(d.last_checked);checkInfo.textContent='공개 보도 자동 확인: 매일 1회 · 최근 확인 '+(Number.isNaN(date.getTime())?d.last_checked:date.toLocaleString('ko-KR'))+' · 추정치 자동 변경 없음';}}catch(e){}}
 updateBorderCheck();
 const source=node('a','','관련 공개 분석 검색 (38 North)');source.href='https://www.38north.org/?s=border+fence';source.target='_blank';source.rel='noopener noreferrer';borderPanel.append(source);right.append(borderPanel);
 const navyPanel=node('div','nbm-border-panel');navyPanel.id='nbm-navy-panel';navyPanel.setAttribute('role','tabpanel');navyPanel.append(node('div','nbm-meta','중국 해군·해경 훈련, 항모 활동, 해상 기동, 합동훈련 · 매일 1회 공개 보도 확인'));
 const navyList=node('div','nbm-list');navyList.append(node('p','nbm-empty','중국 해군 동향 데이터를 불러오는 중입니다.'));navyPanel.append(navyList);right.append(navyPanel);columns.append(right);
 async function loadNavy(){try{const r=await fetch('./data/china-navy-news.json?ts='+Math.floor(Date.now()/3600000),{cache:'no-store'});if(!r.ok)throw Error('아직 수집되지 않음');const d=await r.json();navyList.replaceChildren();const checked=d.last_checked?new Date(d.last_checked).toLocaleString('ko-KR'):'확인 전';navyList.append(node('p','nbm-meta','최근 확인 '+checked+' · 수집 기사 '+(d.items||[]).length+'건'));for(const a of (d.items||[]).slice(0,30)){const item=node('div','nbm-item');const title=node('span','',a.title_ko||a.title||'제목 없음');if(a.url&&/^https:\/\//.test(a.url)){const link=node('a','',title.textContent);link.href=a.url;link.target='_blank';link.rel='noopener noreferrer';item.append(link)}else item.append(title);if(a.category)item.append(node('span','nbm-source',a.category));navyList.append(item)}if(!(d.items||[]).length)navyList.append(node('p','nbm-empty','현재 수집된 관련 보도가 없습니다.'))}catch(e){navyList.replaceChildren(node('p','nbm-empty','첫 수집 대기 중입니다. GitHub Actions 실행 후 표시됩니다.'))}}
 loadNavy();
 function showRight(tab){officialMeta.hidden=tab!=='who';officialList.hidden=tab!=='who';borderPanel.hidden=tab!=='border';navyPanel.hidden=tab!=='navy';whoBtn.setAttribute('aria-selected',String(tab==='who'));borderBtn.setAttribute('aria-selected',String(tab==='border'));navyBtn.setAttribute('aria-selected',String(tab==='navy'));}
 whoBtn.addEventListener('click',()=>showRight('who'));borderBtn.addEventListener('click',()=>showRight('border'));navyBtn.addEventListener('click',()=>showRight('navy'));showRight('who');
 function show(book){alerts.hidden=book;bookmarks.hidden=!book;alertBtn.setAttribute('aria-selected',String(!book));bookBtn.setAttribute('aria-selected',String(book))}
 alertBtn.addEventListener('click',()=>show(false));bookBtn.addEventListener('click',()=>show(true));$('nb-bookmark-open')?.addEventListener('click',()=>show(true),{capture:true});show(false);
 document.addEventListener('nb-title-translation-changed',renderOfficial);load();setInterval(load,300000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
