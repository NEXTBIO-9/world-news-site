/* NEXT BIO: official WHO notices + bookmarks, translation toggle integration. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const style=document.createElement('style');style.textContent=`
#nb-bookmark-open{display:none!important}
#nb-intelligence .nbm-tabs{display:flex;gap:12px;overflow-x:auto;scrollbar-width:thin;margin:0 0 9px;border-bottom:1px solid #324760;flex-shrink:0}
#nb-intelligence .nbm-tabs button{appearance:none;border:0;border-bottom:2px solid transparent;border-radius:0;background:transparent;color:#91a9c4;font-size:12px;font-weight:650;padding:8px 2px 10px;white-space:nowrap;flex-shrink:0;cursor:pointer;box-shadow:none}
#nb-intelligence .nbm-tabs button[aria-selected=true]{color:#f0f8ff;border-bottom-color:transparent}
#nb-intelligence .nbm-tabs button{position:relative}
#nb-intelligence .nbm-tabs button[aria-selected=true]::after{content:'';position:absolute;left:0;right:0;bottom:0;height:2px;background:#48cbbb;border-radius:0 0 9px 9px;pointer-events:none}
#nb-intelligence .nbm-tabs button:hover{color:#fff}
#nb-intelligence .nb2-columns{align-items:stretch}
#nb-intelligence .nbm-alerts-panel{height:310px;max-height:310px;min-height:0;box-sizing:border-box;display:flex;flex-direction:column;overflow:hidden}
#nb-intelligence .nbm-alerts-panel>#nb-alerts{display:block;scrollbar-width:thin}
#nb-intelligence .nbm-alerts-panel .nb2-row{padding:7px 0}
#nb-intelligence .nbm-alerts-panel>h3{display:none}
#nb-intelligence .nbm-alerts-panel>#nb-alerts,#nb-intelligence .nbm-alerts-panel>#nb-market-issues,#nb-intelligence .nbm-alerts-panel>#nb-risk-signals,#nb-intelligence .nbm-alerts-panel>#nb-global-calendar,#nb-intelligence .nbm-alerts-panel>#nb-country-anomaly{flex:1;min-height:0;overflow-y:auto}
#nb-intelligence .nbm-alerts-panel>#nb-bookmarks{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;margin:0;padding:0;border:0;background:transparent;max-height:none;height:auto}
#nb-intelligence .nbm-alerts-panel>#nb-global-calendar[hidden],#nb-intelligence .nbm-alerts-panel>#nb-country-anomaly[hidden],#nb-intelligence .nbm-alerts-panel>#nb-risk-signals[hidden],#nb-intelligence .nbm-alerts-panel>#nb-market-issues[hidden],#nb-intelligence .nbm-alerts-panel>#nb-bookmarks[hidden],#nb-intelligence .nbm-alerts-panel>#nb-alerts[hidden]{display:none!important}
#nb-intelligence .nbm-alerts-panel>#nb-bookmarks>h3{display:none}
#nb-intelligence .nbm-alerts-panel #nb-saved-list{flex:1;min-height:0;overflow-y:auto;max-height:none;grid-template-columns:minmax(0,1fr)}
#nb-intelligence .nbm-alerts-panel .nb-scrap-toolbar{min-width:0;flex-shrink:0}
#nb-intelligence .nbm-alerts-panel .nb-scrap-toolbar>*{max-width:100%}
#nb-intelligence .nbm-official{height:310px;max-height:310px;min-height:0;display:flex;flex-direction:column;overflow:hidden;padding:12px 14px;border:1px solid var(--border,#334155);border-radius:7px;box-sizing:border-box}
#nb-intelligence .nbm-official h3{margin:0 0 6px;font-size:14px}
#nb-intelligence .nbm-official-tabs{display:flex;gap:12px;flex-wrap:wrap;border-bottom:1px solid #324760;margin-bottom:9px;flex-shrink:0}
#nb-intelligence .nbm-official-tabs button{background:transparent;border:0;border-bottom:2px solid transparent;color:#91a9c4;padding:5px 0 9px;cursor:pointer;font-size:12px;font-weight:700}
#nb-intelligence .nbm-official-tabs button[aria-selected=true]{color:#f0f8ff;border-bottom-color:transparent}
#nb-intelligence .nbm-official-tabs button{position:relative}
#nb-intelligence .nbm-official-tabs button[aria-selected=true]::after{content:'';position:absolute;left:0;right:0;bottom:0;height:2px;background:#48cbbb;border-radius:0 0 9px 9px;pointer-events:none}
#nb-intelligence .nbm-border-panel{flex:1;min-height:0;overflow-y:auto;color:#d9e9fa;font-size:12px;line-height:1.65}
#nb-intelligence #nbm-navy-panel[hidden],
#nb-intelligence #nbm-blood-panel .nbm-blood-hero{display:flex;align-items:center;justify-content:space-between;gap:12px;background:linear-gradient(120deg,#243b57,#1b2d43);border:1px solid #46617e;border-radius:10px;padding:11px 13px;margin:7px 0 10px}
#nb-intelligence #nbm-blood-panel .nbm-blood-hero small{display:block;color:#a9bfd6;font-size:10px;letter-spacing:.3px}
#nb-intelligence #nbm-blood-panel .nbm-blood-value{font-size:27px;font-weight:800;letter-spacing:-.7px;line-height:1.2;color:#f5f9ff}
#nb-intelligence #nbm-blood-panel .nbm-blood-value span{font-size:12px;color:#b3c7dd;font-weight:500;margin-left:3px}
#nb-intelligence #nbm-blood-panel .nbm-blood-badge{display:inline-flex;border-radius:99px;padding:5px 11px;background:#514027;color:#ffd48d;border:1px solid #967142;font-size:11px;font-weight:750;white-space:nowrap}
#nb-intelligence #nbm-blood-panel .nbm-blood-badge[data-stage="적정"]{background:#173f39;color:#9ae8cb;border-color:#397e6a}
#nb-intelligence #nbm-blood-panel .nbm-blood-badge[data-stage="주의"],#nb-intelligence #nbm-blood-panel .nbm-blood-badge[data-stage="경계"],#nb-intelligence #nbm-blood-panel .nbm-blood-badge[data-stage="심각"]{background:#572e37;color:#ffb4c2;border-color:#9a4e60}
#nb-intelligence #nbm-blood-panel .nbm-blood-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-bottom:9px}
#nb-intelligence #nbm-blood-panel .nbm-blood-type{background:#22354c;border:1px solid #3c536d;border-radius:8px;padding:8px 7px;min-width:0}
#nb-intelligence #nbm-blood-panel .nbm-blood-type-label{color:#b8cbe0;font-size:11px;font-weight:700}
#nb-intelligence #nbm-blood-panel .nbm-blood-type-number{color:#f4f9ff;font-size:17px;font-weight:800;line-height:1.3;margin:2px 0}
#nb-intelligence #nbm-blood-panel .nbm-blood-type-number span{font-size:10px;font-weight:400;color:#9bb3ce}
#nb-intelligence #nbm-blood-panel .nbm-blood-type-stage{font-size:10px;color:#e7bc79}
#nb-intelligence #nbm-blood-panel .nbm-blood-type-stage[data-stage="적정"]{color:#88d6b8}
#nb-intelligence #nbm-blood-panel .nbm-blood-type-stage[data-stage="주의"],#nb-intelligence #nbm-blood-panel .nbm-blood-type-stage[data-stage="경계"],#nb-intelligence #nbm-blood-panel .nbm-blood-type-stage[data-stage="심각"]{color:#ff9cae}
#nb-intelligence #nbm-blood-panel .nbm-blood-foot{font-size:10px;color:#91a9c4;line-height:1.6;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}
#nb-intelligence #nbm-blood-panel .nbm-blood-foot a{font-size:10px;text-decoration:none}
@media(max-width:460px){#nb-intelligence #nbm-blood-panel .nbm-blood-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}

#nb-intelligence #nbm-mps-panel .nbm-mps-summary{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:7px 0 10px;color:#a6bed8;font-size:10px}
#nb-intelligence #nbm-mps-panel .nbm-mps-count{padding:3px 9px;border-radius:99px;border:1px solid #48627e;background:#243850;color:#d9eafd;white-space:nowrap;font-weight:700}
#nb-intelligence #nbm-mps-panel .nbm-mps-timeline{position:relative;margin:2px 0 0 6px;padding:0 0 0 19px;border-left:1px solid #476482}
#nb-intelligence #nbm-mps-panel .nbm-mps-event{position:relative;padding:1px 0 13px;margin-bottom:8px;border-bottom:1px solid #354b65}
#nb-intelligence #nbm-mps-panel .nbm-mps-event:last-child{margin-bottom:0;border-bottom:0}
#nb-intelligence #nbm-mps-panel .nbm-mps-event:before{content:'';position:absolute;left:-25px;top:5px;width:9px;height:9px;border:2px solid #7acde9;background:#1c2b40;border-radius:50%;box-sizing:border-box;box-shadow:0 0 0 3px #1c2b40}
#nb-intelligence #nbm-mps-panel .nbm-mps-date{color:#78cbe9;font-size:11px;font-weight:700;letter-spacing:.1px}
#nb-intelligence #nbm-mps-panel .nbm-mps-place{color:#eaf3ff;font-size:12px;font-weight:750;margin:2px 0}
#nb-intelligence #nbm-mps-panel .nbm-mps-link{display:block;color:#bbd8f6;font-size:11px;line-height:1.5;text-decoration:none}
#nb-intelligence #nbm-mps-panel .nbm-mps-link:hover{text-decoration:underline;color:#fff}
#nb-intelligence #nbm-mps-panel .nbm-mps-tag{display:inline-block;margin-top:5px;padding:2px 7px;background:#233b51;border:1px solid #385c72;border-radius:4px;color:#a7d7e5;font-size:10px}
#nb-intelligence #nbm-mps-panel .nbm-mps-note{font-size:10px;color:#89a5c2;margin-top:8px}

#nb-intelligence #nbm-gnss-panel .nbm-gnss-head{display:flex;justify-content:space-between;align-items:center;gap:9px;margin:6px 0 9px}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-eyebrow{color:#91a6ba;font:10px ui-monospace,Consolas,monospace;letter-spacing:1px}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-heading{color:#edf3fa;font-size:14px;font-weight:750;margin-top:3px}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-count{color:#c4d2e0;font:10px ui-monospace,Consolas,monospace;padding:5px 8px;border:1px solid #41546a;border-radius:4px;white-space:nowrap}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-card{border:1px solid #35495d;border-radius:7px;background:#172637;padding:10px 12px;margin:0 0 10px}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-meta{display:flex;justify-content:space-between;gap:10px}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-label{color:#849ab0;font:9px ui-monospace,Consolas,monospace;letter-spacing:.7px}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-code{font:700 18px ui-monospace,Consolas,monospace;color:#f2f7fc;margin-top:3px}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-region{font:600 11px ui-monospace,Consolas,monospace;color:#d5e0ec;margin-top:5px;text-align:right}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-chartlabel{display:flex;justify-content:space-between;gap:8px;margin:10px 0 5px}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-chart{height:48px;display:flex;align-items:flex-end;gap:2px;overflow:hidden;padding:4px 4px 0;border-bottom:1px solid #354b5d;background:repeating-linear-gradient(to bottom,transparent 0,transparent 14px,#ffffff0a 15px)}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-bar{flex:1;min-width:1px;background:#7696aa;border-radius:1px 1px 0 0;transform-origin:bottom;animation:nbm-spectrum 4s ease-in-out infinite alternate}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-bar:nth-child(5n){background:#b5a47b}
@keyframes nbm-spectrum{0%{transform:scaleY(.87);opacity:.7}50%{transform:scaleY(1.06);opacity:.96}100%{transform:scaleY(.93);opacity:.83}}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-dates{display:flex;justify-content:space-between;gap:10px;margin-top:9px;color:#c5d3e2;font:10px ui-monospace,Consolas,monospace}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-entries{max-height:120px;overflow-y:auto;scrollbar-width:thin}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-entry{padding:6px 0;border-top:1px solid #2e4358;font-size:11px}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-entry a{color:#b5d1e8;text-decoration:none}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-entry a:hover{text-decoration:underline}
#nb-intelligence #nbm-gnss-panel .nbm-gnss-entry small{display:block;color:#849db6;font-size:10px;margin-top:3px}
@media(prefers-reduced-motion:reduce){#nb-intelligence #nbm-gnss-panel .nbm-gnss-bar{animation:none}}
#nb-intelligence .nbm-border-panel[hidden],#nb-intelligence .nbm-official .nbm-list[hidden],#nb-intelligence .nbm-official .nbm-meta[hidden]{display:none!important}
#nb-intelligence .nbm-forecast-summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:10px}
#nb-intelligence .nbm-forecast-summary .nbm-border-status{margin:0;min-width:0}
#nb-intelligence .nbm-forecast-details{border-top:1px solid #3a536e;padding:8px 0}
#nb-intelligence .nbm-forecast-details>summary{cursor:pointer;font-size:12px;font-weight:750;color:#e5f2ff;list-style-position:inside;padding:3px 0}
#nb-intelligence .nbm-forecast-details[open]>summary{margin-bottom:8px}
#nb-intelligence .nbm-forecast-details .nbm-border-panel{overflow:visible;border:0!important;margin:0!important;padding:0!important}
#nb-intelligence .nbm-forecast-details .nbm-section-heading{display:none}
#nb-intelligence .nbm-forecast-details .nbm-border-status{padding:7px 9px;margin:6px 0}
#nb-intelligence .nbm-forecast-details .nbm-border-panel p{margin:6px 0}
#nb-intelligence .nbm-forecast-details .nbm-progress-track{margin:4px 0;height:6px}
@media(max-width:560px){#nb-intelligence .nbm-forecast-summary{grid-template-columns:minmax(0,1fr)}}
#nb-intelligence .nbm-section-heading{font-size:13px;font-weight:750;color:#e5f2ff;margin:0 0 8px;line-height:1.4}
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
 const alertBtn=node('button','','⚡ 신규·주요 뉴스'),marketBtn=node('button','','📈 글로벌 증시 주요 이슈'),riskBtn=node('button','','🚨 글로벌 위험 신호'),calendarBtn=node('button','','📅 글로벌 주요 일정');
 for(const b of [alertBtn,marketBtn,riskBtn,calendarBtn]){b.type='button';b.setAttribute('role','tab')}
 tabs.append(alertBtn,marketBtn,riskBtn,calendarBtn);left.insertBefore(tabs,alerts);const marketList=node('div','nb2-list');marketList.id='nb-market-issues';marketList.hidden=true;left.append(marketList);const riskList=node('div','nb2-list');riskList.id='nb-risk-signals';riskList.hidden=true;left.append(riskList);const calendarList=node('div','nb2-list');calendarList.id='nb-global-calendar';calendarList.hidden=true;left.append(calendarList);bookmarks.hidden=true;bookmarks.style.display='none';
 for(const s of [...columns.children])if(s!==left)s.remove();
 const right=node('section','nbm-official');right.id='nbm-official';
 const rightTabs=node('div','nbm-official-tabs');rightTabs.setAttribute('role','tablist');rightTabs.setAttribute('aria-label','공식 감염병 발표, 동아시아 안보 동향 및 해상사전배치전단 및 GNSS 교란 및 혈액 수급 공개 기록');
 const whoBtn=node('button','','🏥 공식 감염병 발표'),forecastBtn=node('button','','🌏 동아시아 안보 동향'),mpsBtn=node('button','','🚢 미군 사전배치전단'),gnssBtn=node('button','','📡 동북아 GPS 교란 경보'),bloodBtn=node('button','','🩸 국내 혈액 수급 경보'),manualBtn=node('button','','NEXT 썰');
 for(const b of [whoBtn,forecastBtn,mpsBtn,gnssBtn,bloodBtn,manualBtn]){b.type='button';b.setAttribute('role','tab');rightTabs.append(b)}right.append(rightTabs);
 officialMeta=node('div','nbm-meta','WHO 공식 발표 · 제목 번역 ON/OFF 연동');right.append(officialMeta);
 officialList=node('div','nbm-list');right.append(officialList);
 const manualPanel=node('div','nbm-list');manualPanel.id='nbm-manual-panel';manualPanel.setAttribute('role','tabpanel');manualPanel.hidden=true;manualPanel.append(node('p','nbm-empty','자체 발행 기사를 불러오는 중입니다.'));right.append(manualPanel);
 async function loadManual(){try{
  const r=await fetch('./data/manual-articles.json?v='+Math.floor(Date.now()/300000),{cache:'no-store'});
  if(!r.ok)throw Error('HTTP '+r.status);
  const d=await r.json();
  const items=(Array.isArray(d.articles)?d.articles:[]).filter(a=>a&&a.manual===true&&Number.isSafeInteger(a.manual_issue)&&a.title).sort((a,b)=>(Date.parse(b.published||'')||0)-(Date.parse(a.published||'')||0));
  manualPanel.replaceChildren();
  if(!items.length){manualPanel.append(node('p','nbm-empty','아직 자체 발행 기사가 없습니다.'));return}
  for(const a of items){
   const item=node('div','nbm-item');
   const link=node('a','',String(a.title_ko||a.title));
   link.href='./article.html?id='+encodeURIComponent(a.manual_issue);
   item.append(link);
   manualPanel.append(item);
  }
 }catch{manualPanel.replaceChildren(node('p','nbm-empty','자체 발행 기사 데이터를 불러오지 못했습니다.'))}}
 loadManual();setInterval(loadManual,300000);
 const borderPanel=node('div','nbm-border-panel');borderPanel.id='nbm-border-panel';borderPanel.setAttribute('role','group');borderPanel.setAttribute('aria-label','북한 장벽 요새화 현황');
 borderPanel.append(node('h3','nbm-section-heading','🧱 북한 장벽 요새화 현황'));
 borderPanel.append(node('div','nbm-meta','남북 접경지역 요새화 · 2026년 8월 기준 보도 추정치'));
 const estimatesBox=node('div','');borderPanel.append(estimatesBox);
 const estimateNote=node('p','','※ 남북 접경지역의 과거 보도 추정치이며 중국·러시아 접경지역 전체 완공률이나 공식 확정 수치가 아닙니다.');borderPanel.append(estimateNote);
 const checkInfo=node('p','nbm-meta','공개 보도 확인 정보 로딩 중');borderPanel.append(checkInfo);
 const addEstimate=(label,value,pct,note)=>{const wrap=node('div','nbm-border-status');wrap.append(node('span','',label+' · 보도 추정치'));wrap.append(node('strong','',value));const track=node('div','nbm-progress-track');const fill=node('div','nbm-progress-fill');fill.style.width=Math.max(0,Math.min(100,pct))+'%';track.append(fill);wrap.append(track);wrap.append(node('span','',note));estimatesBox.append(wrap)};
 function showEstimates(e){
  estimatesBox.replaceChildren();
  const ground=Number(e?.ground_preparation_pct),low=Number(e?.fences_mines_pct_min),high=Number(e?.fences_mines_pct_max);
  if(!Number.isFinite(ground)||!Number.isFinite(low)||!Number.isFinite(high)||ground<0||ground>100||low<0||high>100||low>high){estimatesBox.append(node('p','nbm-empty','추정치 데이터 검증이 필요합니다.'));return}
  addEstimate('지면 정리 작업','약 '+ground+'%',ground,'전체 장벽 완공률이 아닌 해당 구간 보도 추정');
  addEstimate('철책·지뢰지대 구축','약 '+low+'~'+high+'%',high,'구간별 추정 범위 · 막대는 상한을 표시');
  const period=String(e.reference_period||'기준일 미상');
  estimateNote.textContent='※ '+period+' 기준 공개 보도 추정치입니다. 남북 접경지역 일부 구간에 관한 수치로, 공식 확정치나 실시간 측정값이 아닙니다.';
 }
 async function updateBorderCheck(){try{const r=await fetch('./data/nk-border-status.json?ts='+Math.floor(Date.now()/3600000),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();showEstimates(d.estimates);const date=d.last_checked?new Date(d.last_checked):null;const checked=date&&!Number.isNaN(date.getTime())?date.toLocaleString('ko-KR'):'확인 시각 미상';const evidence=Array.isArray(d.estimate_evidence)?d.estimate_evidence:[];checkInfo.textContent='공개 보도 자동 확인: 매일 1회 · 최근 확인 '+checked+' · 수치 갱신은 검증된 근거가 등록된 경우에만 적용';if(evidence.length){const latest=evidence[evidence.length-1];if(latest&&typeof latest.url==='string'&&/^https:\/\//.test(latest.url)){const link=node('a','','최근 수치 근거 확인');link.href=latest.url;link.target='_blank';link.rel='noopener noreferrer';checkInfo.append(' · ',link)}}}catch(e){checkInfo.textContent='공개 보도 확인 정보를 불러오지 못했습니다.';estimatesBox.replaceChildren(node('p','nbm-empty','추정치 데이터를 불러오지 못했습니다.'))}}
 updateBorderCheck();
 const source=node('a','','관련 공개 분석 검색 (38 North)');source.href='https://www.38north.org/?s=border+fence';source.target='_blank';source.rel='noopener noreferrer';borderPanel.append(source);borderPanel.style.cssText='padding:10px 0 4px;border-top:1px solid #3a536e;margin-top:8px';
 const forecastPanel=node('div','nbm-border-panel');forecastPanel.id='nbm-forecast-panel';forecastPanel.setAttribute('role','tabpanel');
 const nk=node('div','nbm-border-status');nk.style.cssText='padding:8px 10px;margin:0;min-height:0;display:flex;flex-direction:column;gap:2px';nk.append(node('div','','🧱 북한 국경 장벽'),node('div','nbm-meta','한국 합동참모본부 공식 전망'),node('strong','','2028년 하반기 완공 예상'),node('p','','2026년 10월 8일 합참 국정감사 발표 기준'));forecastPanel.append(nk);
 const cn=node('div','nbm-border-status');cn.style.cssText='padding:8px 10px;margin:0;min-height:0;display:flex;flex-direction:column;gap:2px';cn.append(node('div','','⚓ 중국 해군 동향'),node('div','nbm-meta','대만 전면 침공 위험 관찰 시점'),node('strong','','2028년 이후'),node('p','','미국 당국자 평가에 근거한 관찰 구간. 실제 침공 예정일은 확인되지 않음.'));forecastPanel.append(cn);
 const forecastSummary=node('div','nbm-forecast-summary');forecastSummary.append(nk,cn);forecastPanel.prepend(forecastSummary);
 for(const card of [nk,cn]){const strong=card.querySelector('strong');if(strong)strong.style.cssText='font-size:15px;line-height:1.25;margin:2px 0';const para=card.querySelector('p');if(para)para.style.cssText='margin:2px 0 0;font-size:11px;line-height:1.35'}
 forecastPanel.style.cssText='padding:6px 0';
 const borderDetails=node('details','nbm-forecast-details');borderDetails.append(node('summary','','🧱 북한 장벽 요새화 현황 · 자세히 보기'),borderPanel);forecastPanel.append(borderDetails);right.append(forecastPanel);
 const mpsPanel=node('div','nbm-border-panel');mpsPanel.id='nbm-mps-panel';mpsPanel.setAttribute('role','tabpanel');mpsPanel.hidden=true;
 mpsPanel.append(node('h3','nbm-section-heading','🚢 동북아 미군 해상사전배치전단 · 최대 10건'));
 mpsPanel.append(node('p','nbm-meta','한국·일본 지역 · 공식 발표에 나온 과거 활동 기록 · 실시간 위치 정보 아님'));
 const mpsRecords=[
  {date:'2026-06-13',place:'일본 오키나와 긴만',ship:'USNS 1st LT Jack Lummus',activity:'Freedom Banner 관련 입항',url:'https://www.dvidshub.net/news/568346/usns-lummus-arrives-okinawa-participate-freedom-banner-mpsron-3-group-sail'},
  {date:'2026-06-30 ~ 07-03',place:'한국 포항 인근 해상',ship:'MPSRON-3 소속 선박들',activity:'해상 합동훈련 (항구 입항 아님)',url:'https://www.dvidshub.net/news/printable/570560'}
 ];
 const mpsSummary=node('div','nbm-mps-summary');const mpsSummaryLabel=node('span','','공개 발표 기반 활동 기록');const mpsCount=node('span','nbm-mps-count','02 RECORDS');mpsSummary.append(mpsSummaryLabel,mpsCount);mpsPanel.append(mpsSummary);
 const mpsList=node('div','nbm-mps-timeline');mpsList.style.cssText='max-height:185px;overflow-y:auto;scrollbar-width:thin';mpsPanel.append(mpsList);
 function mpsEvent(a){
  const event=node('div','nbm-mps-event');const date=String(a.date||a.published||'날짜 미상');const place=String(a.place||'활동 장소는 원문에서 확인');
  event.append(node('div','nbm-mps-date',date),node('div','nbm-mps-place',place));
  const title=a.ship?String(a.ship)+' — '+String(a.activity||'공개 활동'):String(a.title||'공식 발표');
  if(typeof a.url==='string'&&/^https:\/\//.test(a.url)){const link=node('a','nbm-mps-link',title);link.href=a.url;link.target='_blank';link.rel='noopener noreferrer';event.append(link)}else event.append(node('div','nbm-mps-link',title));
  event.append(node('span','nbm-mps-tag',a.activity?(a.activity.includes('입항 아님')?'해상훈련 · 입항 아님':a.activity.includes('입항')?'입항 기록':'공식 활동 기록'):'공개 발표 · 위치 원문 확인'));
  return event;
 }
 function renderMps(entries,label){
  mpsList.replaceChildren();for(const a of entries.slice(0,10))mpsList.append(mpsEvent(a));
  mpsCount.textContent=String(Math.min(entries.length,10)).padStart(2,'0')+' RECORDS';mpsSummaryLabel.textContent=label;
 }
 renderMps([...mpsRecords].sort((x,y)=>y.date.localeCompare(x.date)),'미군 공식 발표 · 과거 활동');
 async function loadMpsNews(){try{
  const response=await fetch('./data/mpsron-news.json?ts='+Math.floor(Date.now()/3600000),{cache:'no-store'});
  if(!response.ok)throw Error('No report index yet');
  const data=await response.json();const entries=Array.isArray(data.items)?data.items.slice(0,10):[];
  if(!entries.length)return;
  const checked=data.last_checked?new Date(data.last_checked).toLocaleString('ko-KR'):'확인 전';
  renderMps(entries,'공개 발표 관련 보도 · 최근 확인 '+checked);
 }catch{ /* Keep curated confirmed records until the first scheduled run. */ }}
 loadMpsNews();setInterval(loadMpsNews,3600000);
 mpsPanel.append(node('p','nbm-mps-note','※ 마지막 공개 확인 장소는 현재 정박지·항해 위치를 의미하지 않습니다. 새로운 발표는 검증 후 추가해야 합니다.'));
 right.append(mpsPanel);
 const gnssPanel=node('div','nbm-border-panel');gnssPanel.id='nbm-gnss-panel';gnssPanel.setAttribute('role','tabpanel');gnssPanel.hidden=true;
 const gnssHead=node('div','nbm-gnss-head');const gnssHeadLeft=node('div','');gnssHeadLeft.append(node('div','nbm-gnss-eyebrow','NEXT BIO / SIGNAL INTELLIGENCE'),node('div','nbm-gnss-heading','GNSS Interference Monitor'));
 const gnssCount=node('span','nbm-gnss-count','— NOTICE');gnssHead.append(gnssHeadLeft,gnssCount);gnssPanel.append(gnssHead);
 const gnssCard=node('div','nbm-gnss-card');const gnssMeta=node('div','nbm-gnss-meta');const gnssCodeWrap=node('div','');gnssCodeWrap.append(node('div','nbm-gnss-label','NOTICE IDENTIFIER'));const gnssCode=node('div','nbm-gnss-code','—');gnssCodeWrap.append(gnssCode);const gnssRegionWrap=node('div','');gnssRegionWrap.append(node('div','nbm-gnss-label','REGION'));const gnssRegion=node('div','nbm-gnss-region','NORTHEAST ASIA');gnssRegionWrap.append(gnssRegion);gnssMeta.append(gnssCodeWrap,gnssRegionWrap);gnssCard.append(gnssMeta);
 const chartLabel=node('div','nbm-gnss-chartlabel');chartLabel.append(node('span','nbm-gnss-label','SPECTRUM VISUALIZATION'),node('span','nbm-gnss-label','SIMULATED / NOT LIVE'));gnssCard.append(chartLabel);
 const chart=node('div','nbm-gnss-chart');chart.setAttribute('aria-hidden','true');
 for(let i=0;i<56;i++){const bar=node('div','nbm-gnss-bar');const peak=Math.exp(-Math.pow((i-17)/7,2))*55+Math.exp(-Math.pow((i-40)/5,2))*42;const variation=(Math.sin(i*2.7)+1)*7;bar.style.height=(10+peak+variation)+'%';bar.style.animationDelay=(-i*.11)+'s';bar.style.animationDuration=(3.1+(i%9)*.19)+'s';chart.append(bar)}
 gnssCard.append(chart);
 const gnssDates=node('div','nbm-gnss-dates');gnssCard.append(gnssDates);gnssPanel.append(gnssCard);
 const gnssList=node('div','nbm-gnss-entries');gnssList.append(node('p','nbm-empty','공개 GNSS 교란 공고를 불러오는 중입니다.'));gnssPanel.append(gnssList);
 right.append(gnssPanel);
 async function loadGnss(){try{
  const response=await fetch('./data/gnss-alerts.json?ts='+Math.floor(Date.now()/3600000),{cache:'no-store'});if(!response.ok)throw Error('HTTP '+response.status);
  const data=await response.json();const items=Array.isArray(data.items)?data.items.slice(0,10):[];
  gnssList.replaceChildren();gnssCount.textContent=String(items.length).padStart(2,'0')+' NOTICE'+(items.length===1?'':'S');
  if(!items.length){gnssCode.textContent='—';gnssDates.replaceChildren();gnssList.append(node('p','nbm-empty','현재 등록된 공고가 없습니다.'));return}
  const first=items[0],firstTitle=String(first.title||'');const code=firstTitle.match(new RegExp('(?:RKRR\\s*)?[A-Z]\\d{4}\\/\\d{2}','i'));gnssCode.textContent=code?code[0].replace(new RegExp('^RKRR\\s*','i'),''):'PUBLIC NOTICE';
  gnssRegion.textContent=/RKRR|인천|Korea|한국/i.test(firstTitle)?'RKRR / INCHEON FIR':/Japan|일본/i.test(firstTitle)?'JAPAN / PUBLIC NOTICE':'NORTHEAST ASIA';
  gnssDates.replaceChildren(node('span','','ISSUED '+String(first.published||'—')),node('span','','PUBLIC NOTICE'));
  for(const a of items){const item=node('div','nbm-gnss-entry');const title=String(a.title||'GNSS 관련 공고');if(typeof a.url==='string'&&/^https:\/\//.test(a.url)){const link=node('a','',title+' ↗');link.href=a.url;link.target='_blank';link.rel='noopener noreferrer';item.append(link)}else item.append(node('span','',title));item.append(node('small','',String(a.published||'날짜 미상')+' · '+String(a.source||'공개 자료')+' · '+String(a.type||'발표')));gnssList.append(item)}
  if(data.last_checked){const d=new Date(data.last_checked);if(!Number.isNaN(d.getTime()))gnssList.append(node('small','nbm-gnss-label','최근 확인 '+d.toLocaleString('ko-KR')))}
 }catch{gnssList.replaceChildren(node('p','nbm-empty','공고 데이터를 불러오지 못했습니다.'))}}
 loadGnss();setInterval(loadGnss,3600000);
 const bloodPanel=node('div','nbm-border-panel');bloodPanel.id='nbm-blood-panel';bloodPanel.setAttribute('role','tabpanel');bloodPanel.hidden=true;
 bloodPanel.append(node('h3','nbm-section-heading','🩸 국내 혈액 수급 경보'));
 bloodPanel.append(node('p','nbm-meta','대한적십자사 적혈구제제 보유일수 · 매일 공개 자료 확인 · 실시간 수치 아님'));
 const bloodList=node('div','nbm-list');bloodList.style.cssText='min-height:0;overflow:visible;max-height:none';bloodList.append(node('p','nbm-empty','혈액 수급 자료를 불러오는 중입니다.'));bloodPanel.append(bloodList);
 right.append(bloodPanel);
 function bloodStage(days){return days>=5?'적정':days>=3?'관심':days>=2?'주의':days>=1?'경계':'심각'}
 async function loadBlood(){try{
  const response=await fetch('./data/blood-supply.json?ts='+Math.floor(Date.now()/3600000),{cache:'no-store'});if(!response.ok)throw Error('HTTP '+response.status);
  const data=await response.json();bloodList.replaceChildren();
  if(typeof data.total_days!=='number'||!data.observation_date){bloodList.append(node('p','nbm-empty','공식 보유량 확인 대기 중입니다.'));return}
  const stage=bloodStage(data.total_days);
  const hero=node('div','nbm-blood-hero');const valueWrap=node('div','');
  valueWrap.append(node('small','','전국 적혈구 보유량'));
  const value=node('div','nbm-blood-value',data.total_days.toFixed(1));value.append(node('span','','일분'));valueWrap.append(value);
  const badge=node('span','nbm-blood-badge',stage+' 단계');badge.dataset.stage=stage;hero.append(valueWrap,badge);bloodList.append(hero);
  const grid=node('div','nbm-blood-grid');const types=data.blood_types||{};
  for(const t of ['A','B','O','AB']){
   const tile=node('div','nbm-blood-type');tile.append(node('div','nbm-blood-type-label',t+'형'));
   if(typeof types[t]==='number'){const n=node('div','nbm-blood-type-number',types[t].toFixed(1));n.append(node('span','','일'));tile.append(n);const st=bloodStage(types[t]);const label=node('div','nbm-blood-type-stage',st);label.dataset.stage=st;tile.append(label)}
   else tile.append(node('div','nbm-blood-type-number','—'));
   grid.append(tile);
  }
  bloodList.append(grid);
  const foot=node('div','nbm-blood-foot');
  foot.append(node('span','','기준 '+data.observation_date+' · '+(data.status==='ok'?'공식 확인':data.status==='seed'?'초기 자료':'이전 자료 · 갱신 확인 필요')));
  const a=node('a','','대한적십자사 원문 ↗');a.href='https://www.bloodinfo.net/knrcbs/bi/info/bldHoldSttus.do?mi=1046';a.target='_blank';a.rel='noopener noreferrer';foot.append(a);bloodList.append(foot);
 }catch{bloodList.replaceChildren(node('p','nbm-empty','자료를 불러오지 못했습니다.'))}}
 loadBlood();setInterval(loadBlood,3600000);
 const navyPanel=node('div','nbm-border-panel');navyPanel.id='nbm-navy-panel';navyPanel.setAttribute('role','group');navyPanel.setAttribute('aria-label','중국 해군 최신 동향');navyPanel.append(node('h3','nbm-section-heading','⚓ 중국 해군 최신 동향'));navyPanel.append(node('div','nbm-meta','중국 해군·해경 훈련, 항모 활동, 해상 기동, 합동훈련 · 매일 1회 공개 보도 확인'));
 const navyList=node('div','nbm-list');navyList.append(node('p','nbm-empty','중국 해군 동향 데이터를 불러오는 중입니다.'));navyPanel.append(navyList);navyPanel.style.cssText='padding:10px 0 4px;border-top:1px solid #3a536e;margin-top:8px';const navyDetails=node('details','nbm-forecast-details');navyDetails.append(node('summary','','⚓ 중국 해군 최신 동향 · 최대 10건'),navyPanel);forecastPanel.append(navyDetails);columns.append(right);
 async function loadNavy(){try{const r=await fetch('./data/china-navy-news.json?ts='+Math.floor(Date.now()/3600000),{cache:'no-store'});if(!r.ok)throw Error('아직 수집되지 않음');const d=await r.json();navyList.replaceChildren();const checked=d.last_checked?new Date(d.last_checked).toLocaleString('ko-KR'):'확인 전';navyList.append(node('p','nbm-meta','최근 확인 '+checked+' · 최신 최대 10건 표시 (수집 '+(d.items||[]).length+'건)'));for(const a of (d.items||[]).slice(0,10)){const item=node('div','nbm-item');const title=node('span','',a.title_ko||a.title||'제목 없음');if(a.url&&/^https:\/\//.test(a.url)){const link=node('a','',title.textContent);link.href=a.url;link.target='_blank';link.rel='noopener noreferrer';item.append(link)}else item.append(title);if(a.category)item.append(node('span','nbm-source',a.category));navyList.append(item)}if(!(d.items||[]).length)navyList.append(node('p','nbm-empty','현재 수집된 관련 보도가 없습니다.'))}catch(e){navyList.replaceChildren(node('p','nbm-empty','첫 수집 대기 중입니다. GitHub Actions 실행 후 표시됩니다.'))}}
 loadNavy();
 function showRight(tab){officialMeta.hidden=tab!=='who';officialList.hidden=tab!=='who';forecastPanel.hidden=tab!=='forecast';manualPanel.hidden=tab!=='manual';mpsPanel.hidden=tab!=='mps';gnssPanel.hidden=tab!=='gnss';bloodPanel.hidden=tab!=='blood';whoBtn.setAttribute('aria-selected',String(tab==='who'));forecastBtn.setAttribute('aria-selected',String(tab==='forecast'));manualBtn.setAttribute('aria-selected',String(tab==='manual'));mpsBtn.setAttribute('aria-selected',String(tab==='mps'));gnssBtn.setAttribute('aria-selected',String(tab==='gnss'));bloodBtn.setAttribute('aria-selected',String(tab==='blood'));}
 whoBtn.addEventListener('click',()=>showRight('who'));forecastBtn.addEventListener('click',()=>showRight('forecast'));manualBtn.addEventListener('click',()=>showRight('manual'));mpsBtn.addEventListener('click',()=>showRight('mps'));gnssBtn.addEventListener('click',()=>showRight('gnss'));bloodBtn.addEventListener('click',()=>showRight('blood'));showRight('who');
 function show(tab){alerts.hidden=tab!=='alerts';marketList.hidden=tab!=='market';riskList.hidden=tab!=='risk';calendarList.hidden=tab!=='calendar';alertBtn.setAttribute('aria-selected',String(tab==='alerts'));marketBtn.setAttribute('aria-selected',String(tab==='market'));riskBtn.setAttribute('aria-selected',String(tab==='risk'));calendarBtn.setAttribute('aria-selected',String(tab==='calendar'))}
 alertBtn.addEventListener('click',()=>show('alerts'));marketBtn.addEventListener('click',()=>show('market'));riskBtn.addEventListener('click',()=>show('risk'));calendarBtn.addEventListener('click',()=>show('calendar'));show('alerts');
 // Repaint after creating the tab containers; the news feed may have rendered earlier.
 window.NB2?.refresh?.();
 document.addEventListener('nb-title-translation-changed',renderOfficial);load();setInterval(load,300000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
