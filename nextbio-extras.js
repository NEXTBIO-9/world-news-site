/* NEXT BIO 2.0: non-destructive extension of existing app.js */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,val)=>{try{localStorage.setItem(key,JSON.stringify(val))}catch{}};
let bookmarks=read('nb2-bookmarks',{}),lang=read('nb2-language','ko'),showSaved=true,heatLayer=null,lastList=[],lastAll=[];
const labels={ko:{saved:'북마크',period:'기간',from:'시작일',to:'종료일',heat:'뉴스 밀도 지도',alerts:'신규·주요 뉴스',bio:'바이오 대시보드',empty:'표시할 뉴스가 없습니다.',clear:'초기화',all:'전체 기간',hours:'최근 24시간',days3:'최근 3일',days7:'최근 7일',days30:'최근 30일',notice:'속보 표시는 수집된 기사 제목과 시간에 기반한 자동 분류이며, 공식 긴급재난 알림이 아닙니다.'},en:{saved:'Bookmarks',period:'Period',from:'From',to:'To',heat:'News density overlay',alerts:'New & important stories',bio:'Biotech dashboard',empty:'No matching articles.',clear:'Reset',all:'All dates',hours:'Last 24 hours',days3:'Last 3 days',days7:'Last 7 days',days30:'Last 30 days',notice:'Breaking labels are automated based on article timestamps and headlines, not official emergency alerts.'}};
const tr=k=>labels[lang]?.[k]||labels.ko[k]||k;
const validDate=a=>{const d=new Date(a.published);return Number.isFinite(d.getTime())?d:null};
function dateOK(a){const d=validDate(a);if(!d)return (!$('nb-date')||$('nb-date').value==='all')&&!$('nb-from')?.value&&!$('nb-to')?.value;const period=$('nb-date')?.value||'all';const now=Date.now();if(period!=='all'&&(d.getTime()<now-Number(period)*86400000||d.getTime()>now+3600000))return false;const start=$('nb-from')?.value||'',end=$('nb-to')?.value||'';const day=d.toISOString().slice(0,10);return (!start||day>=start)&&(!end||day<=end)}
function bio(list){const cats=['미생물','제약·신약','의료기기','바이오기업','감염병'];const counts=cats.map(k=>[k,list.filter(a=>a.category===k).length]);const max=Math.max(1,...counts.map(x=>x[1]));if(!$('nb-bio'))return;$('nb-bio').innerHTML=counts.map(([k,n])=>`<div class="nb2-row">${safe(k)} <span class="nb2-bar" style="width:${Math.round(n/max*42)}%"></span><b>${n}</b></div>`).join('')}
/* Importance scoring applies ONLY to the "New & important" panel.
   Other feeds, country markers, and category filters are unchanged. */
const nbPriorityRules=[
 {points:85,re:/(?:전쟁\s*(?:발발|선포|확전)|침공|대규모\s*(?:공습|폭격|공격)|핵(?:공격|위협)|선전포고|invasion|war\s+(?:breaks?\s+out|declared|escalat)|mass(?:ive)?\s+(?:airstrike|bombing|attack)|nuclear\s+(?:strike|threat))/i},
 {points:80,re:/(?:팬데믹|세계보건기구.{0,25}(?:비상|경보)|국제적\s*공중보건\s*비상|신종\s*(?:감염병|바이러스).{0,25}(?:확산|발생)|pandemic|public\s+health\s+emergency|who\s+declares?.{0,30}emergency|novel\s+(?:virus|pathogen).{0,30}(?:outbreak|spread))/i},
 {points:76,re:/(?:규모\s*[6-9](?:\.[0-9])?\s*지진|대지진|초강력\s*태풍|대형\s*(?:산불|홍수|재난)|수백\s*명\s*사망|earthquake.{0,30}magnitude\s*[6-9]|magnitude\s*[6-9].{0,30}earthquake|major\s+(?:earthquake|flood|wildfire)|catastrophic|hundreds\s+(?:dead|killed))/i},
 {points:72,re:/(?:국가비상사태|계엄령|국경\s*봉쇄|외교관계\s*단절|경제\s*제재|금융\s*위기|은행\s*파산|기준금리\s*(?:인상|인하)|긴급\s*금리|state\s+of\s+emergency|martial\s+law|border\s+closure|diplomatic\s+ties\s+severed|economic\s+sanctions|financial\s+crisis|bank\s+collapse|central\s+bank.{0,30}(?:rate\s+(?:cut|hike)|emergency))/i},
 {points:74,re:/(?:실적\\s*(?:발표|급증|급감|쇼크)|어닝\\s*(?:서프라이즈|쇼크)|주가\\s*(?:급등|급락|폭락)|상장폐지|거래\\s*정지|대규모\\s*(?:인수|합병)|기업\\s*(?:파산|회생)|earnings\\s*(?:beat|miss|surprise)|profit\\s*(?:warning|plunges?|surges?)|shares?\\s*(?:plunge|surge|soar|tumble)|stock\\s*(?:plunge|surge|crash)|merger|acquisition|takeover|bankruptcy|delisting|trading\\s*halt)/i},
 {points:68,re:/(?:군사\s*충돌|미사일\s*발사|무력\s*충돌|휴전\s*붕괴|대규모\s*시위|국가\s*간\s*긴장|military\s+clash|missile\s+launch|armed\s+conflict|ceasefire\s+collapse|mass\s+protests|geopolitical\s+tensions)/i},
 {points:65,re:/(?:집단\s*감염|감염병\s*확산|확진자\s*급증|에볼라\s*확산|콜레라\s*확산|감염병\s*비상|outbreak.{0,35}(?:spreads?|surges?|deaths?|emergency)|surge\s+in\s+(?:cases|infections)|ebola\s+outbreak|cholera\s+outbreak)/i}
];
const nbPriorityContext=/(?:기업|주식|주가|증시|실적|매출|영업이익|인수|합병|상장폐지|거래정지|파산|earnings|shares?|stocks?|equity|merger|acquisition|takeover|bankruptcy|delisting|trading halt|전쟁|군사|분쟁|미사일|공습|폭격|외교|제재|관세|금리|중앙은행|금융|경제위기|지진|태풍|홍수|산불|재난|감염병|에볼라|콜레라|전염병|확진|pandemic|outbreak|military|war|missile|airstrike|sanctions|central bank|financial crisis|earthquake|typhoon|flood|wildfire|ebola|cholera)/i;
const nbPriorityNoise=/(?:연예|스포츠|축구|야구|콘서트|셀럽|할인|쇼핑|레시피|여행\s*추천|행사\s*안내|신제품\s*출시|광고|홍보|celebrity|football|soccer|baseball|concert|shopping|recipe|travel\s+tips|product\s+launch|sponsored|advertorial|promotion)/i;
function nbPriorityScore(a){
 const title=String(a.title||'')+' '+String(a.title_ko||'');
 const cat=String(a.category||'');
 if(nbPriorityNoise.test(title))return 0;
 if(!nbPriorityContext.test(title))return 0;
 let score=0;
 for(const rule of nbPriorityRules)if(rule.re.test(title))score=Math.max(score,rule.points);
 if(!score)return 0; // A generic category or keyword alone never qualifies.
 if(/^(?:분쟁·군사|외교·국제|경제·금융|재해·재난|감염병)$/.test(cat))score+=5;
 const date=validDate(a),age=date?(Date.now()-date.getTime())/3600000:Infinity;
 if(age>=0&&age<=6)score+=5;
 else if(age>=0&&age<=24)score+=3;
 return Math.min(100,score);
}
function nbPriorityKey(a){
 // Remove minor punctuation/stopwords to catch duplicate headlines.
 const t=String(a.title||a.title_ko||'').toLowerCase().replace(/[^\p{L}\p{N}\s]/gu,' ').replace(/\b(?:the|a|an|to|in|of|on|for|and|amid|after|as|at|with)\b/g,' ').replace(/\s+/g,' ').trim();
 return t.slice(0,110)||String(a.url||'');
}
/* Visual event icons only: does not assert that an event is verified. */
function nbAlertIcon(a,score){
 const t=String(a.title||'')+' '+String(a.title_ko||'');
 if(/(?:테러(?:공격|발생|사건)?|terror(?:ist|ism)?\s+(?:attack|bombing)|suicide\s+bombing)/i.test(t))return '💥';
 if(/(?:국가\s*비상사태|비상사태\s*선포|계엄령|state\s+of\s+emergency|martial\s+law)/i.test(t))return '🚨';
 if(/(?:대규모\s*(?:전투|공습|폭격|미사일\s*공격)|massive\s+(?:battle|airstrike|bombardment|missile\s+attack)|major\s+(?:battle|airstrike))/i.test(t))return '🚀';
 if(/(?:전쟁\s*(?:발발|선포|확전)|전면전|침공|war\s+(?:breaks?\s+out|declared|escalat)|full.scale\s+war|invasion)/i.test(t))return '⚔️';
 if(/(?:주가|주식|증시|실적|인수|합병|상장폐지|기업\\s*파산|earnings|shares?|stocks?|merger|acquisition|takeover|bankruptcy|delisting)/i.test(t))return '📈';
 if(/(?:대지진|규모\s*[7-9](?:\.\d+)?\s*지진|초강력\s*태풍|대규모\s*(?:홍수|산불|재난)|major\s+(?:earthquake|flood|wildfire)|catastrophic\s+(?:earthquake|flood|disaster)|magnitude\s*[7-9](?:\.\d+)?\s*earthquake)/i.test(t))return '🌋';
 return score>=70?'⚡':'📰';
}
function alerts(list){
 const now=Date.now(),limit=10;
 const ranked=list.map(a=>({a,score:nbPriorityScore(a),date:validDate(a)}))
  .filter(x=>x.date&&x.date.getTime()<=now+3600000&&x.date.getTime()>=now-7*86400000)
  .sort((x,y)=>y.score-x.score||y.date-x.date);
 const seen=new Set(),chosen=[];
 const add=x=>{const key=nbPriorityKey(x.a);if(seen.has(key)||chosen.length>=limit)return;seen.add(key);chosen.push(x)};
 // Reserve up to two slots for consequential corporate/market developments,
 // without displacing breaking events or fabricating missing stories.
 const market=/기업|주식|주가|증시|실적|매출|영업이익|인수|합병|상장폐지|거래정지|파산|earnings|shares?|stocks?|merger|acquisition|takeover|bankruptcy|delisting|trading halt/i;
 const urgent=ranked.filter(x=>x.score>=80&&x.date.getTime()>=now-48*3600000);
 urgent.slice(0,3).forEach(add);
 const corporate=ranked.filter(x=>x.score>=70&&market.test(String(x.a.title||'')+' '+String(x.a.title_ko||''))&&x.date.getTime()>=now-72*3600000);
 corporate.slice(0,2).forEach(add);
 const priority=ranked.filter(x=>x.score>=70&&x.date.getTime()>=now-48*3600000);
 const recent=[...ranked].sort((x,y)=>y.date-x.date);
 [...priority,...recent].forEach(add);
 const root=$('nb-alerts');if(!root)return;
 root.innerHTML=chosen.length?chosen.map(({a,score})=>`<div class="nb2-row"><span class="nb2-tag">${nbAlertIcon(a,score)+' '}${lang==='ko'?(score>=85?'긴급':score>=70?'주요':'최신'):(score>=85?'Urgent':score>=70?'Priority':'Latest')}${score>=70?' · '+score:''}</span><a target="_blank" rel="noopener noreferrer" href="${safe(/^https?:\/\//i.test(a.url||'')?a.url:'#')}">${safe(window.NBTitleTranslation?.title(a)||(a.title_ko||a.title))}</a></div>`).join(''):`<p class="nb2-muted">${lang==='ko'?'최근 7일간 표시할 뉴스가 없습니다.':'No news available from the past 7 days.'}</p>`;
}
function saveButtons(){
 document.querySelectorAll('#latest-list a.latest-item,#country-feed a.country-item').forEach(a=>{
  const url=a.getAttribute('href');
  if(!/^https?:\/\//i.test(url||''))return;
  // Keep the article and its bookmark button inside the SAME card row.
  // The old version appended a button beside the anchor without a wrapper,
  // leaving the button on a separate line and creating large blank gaps.
  let row=a.parentElement?.classList.contains('nb-news-row')?a.parentElement:null;
  if(!row){row=document.createElement('div');row.className='nb-news-row';a.parentNode.insertBefore(row,a);row.appendChild(a)}
  let btn=Array.from(row.children).find(el=>el.classList.contains('nb2-bookmark'));
  if(!btn){
   const adjacent=row.nextElementSibling;
   if(adjacent?.classList.contains('nb2-bookmark')&&adjacent.dataset.url===url){btn=adjacent;row.appendChild(btn)}
  }
  if(!btn){btn=document.createElement('button');btn.type='button';btn.className='nb2-bookmark';row.appendChild(btn)}
  btn.dataset.url=url;btn.textContent=bookmarks[url]?'★':'☆';btn.title=tr('saved');
  btn.setAttribute('aria-label',tr('saved'));btn.setAttribute('aria-pressed',String(!!bookmarks[url]));
 });
}

function saved(){
 const root=$('nb-saved-list');if(!root)return;
 const query=($('nb-scrap-search')?.value||'').trim().toLocaleLowerCase();
 const folder=$('nb-scrap-folder')?.value||'all';
 const vals=Object.values(bookmarks).filter(a=>a&&/^https?:\/\//i.test(a.url||''))
  .filter(a=>(folder==='all'||(a.folder||'기타')===folder)&&(!query||String(a.title||'').toLocaleLowerCase().includes(query)||String(a.source||'').toLocaleLowerCase().includes(query)))
  .sort((a,b)=>String(b.savedAt||'').localeCompare(String(a.savedAt||'')));
 $('nb-scrap-count').textContent=(lang==='ko'?`저장 ${Object.keys(bookmarks).length}개 · 표시 ${vals.length}개`:`${Object.keys(bookmarks).length} saved · ${vals.length} shown`);
 root.innerHTML=vals.length?vals.map(a=>{
  const date=a.savedAt?new Date(a.savedAt):null;
  const stamp=date&&!isNaN(date)?date.toLocaleDateString(lang==='ko'?'ko-KR':'en-US'):'';
  const folder=a.folder||'기타';
  const opts=['국제·정치','경제','스포츠','과학·기술','기타'].map(x=>`<option value="${safe(x)}" ${x===folder?'selected':''}>${safe(x)}</option>`).join('');
  return `<article class="nb-scrap-card"><div class="nb-scrap-meta"><span>${safe(folder)}</span><span>${safe(a.source||'')}${stamp?' · '+safe(stamp):''}</span></div><a class="nb-scrap-title" href="${safe(a.url)}" target="_blank" rel="noopener noreferrer">${safe(a.title||a.url)}</a><div class="nb-scrap-actions"><label>${lang==='ko'?'폴더':'Folder'} <select class="nb-scrap-assign" data-url="${safe(a.url)}">${opts}</select></label><button type="button" class="nb2-remove" data-url="${safe(a.url)}">${lang==='ko'?'삭제':'Remove'}</button></div></article>`;
 }).join(''):`<p class="nb2-muted">${lang==='ko'?'조건에 맞는 스크랩이 없습니다.':'No matching bookmarks.'}</p>`;
}
function scrapExport(){const data={format:'nextbio-bookmarks',version:1,exportedAt:new Date().toISOString(),bookmarks};const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='nextbio-bookmarks.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}
async function scrapImport(file){
 if(!file)return;
 try{
  if(file.size>2e6)throw Error('File too large');
  const raw=JSON.parse(await file.text());const incoming=raw?.format==='nextbio-bookmarks'?raw.bookmarks:raw;
  if(!incoming||typeof incoming!=='object'||Array.isArray(incoming))throw Error('Invalid format');
  let count=0;
  for(const [key,a] of Object.entries(incoming)){
   if(!a||typeof a!=='object'||typeof a.url!=='string'||!/^https?:\/\//i.test(a.url)||a.url.length>4096)continue;
   if(Object.keys(bookmarks).length>=5000&&!bookmarks[a.url])break;
   bookmarks[a.url]={url:a.url,title:String(a.title||a.url).slice(0,500),folder:['국제·정치','경제','스포츠','과학·기술','기타'].includes(a.folder)?a.folder:'기타',source:String(a.source||'').slice(0,100),savedAt:typeof a.savedAt==='string'?a.savedAt:''};count++;
  }
  write('nb2-bookmarks',bookmarks);syncBookmarkStars();saved();alert(lang==='ko'?`${count}개 항목을 가져왔습니다. (기존 항목은 유지)`: `Imported ${count} items (existing items retained).`);
 }catch(e){alert(lang==='ko'?'올바른 북마크 JSON 파일이 아닙니다.':'Invalid bookmark JSON file.');}
}
function syncBookmarkStars(){document.querySelectorAll('.nb2-bookmark').forEach(b=>{b.textContent=bookmarks[b.dataset.url]?'★':'☆';b.setAttribute('aria-pressed',String(!!bookmarks[b.dataset.url]))})}

function heatmap(groups){if(heatLayer){heatLayer.remove();heatLayer=null}if(!$('nb-heat')?.checked)return;heatLayer=L.layerGroup().addTo(map);const max=Math.max(1,...[...groups.values()].map(a=>a.length));for(const c of countries){const n=groups.get(c[0])?.length||0;if(!n)continue;const intensity=n/max;const circle=L.circleMarker([c[1],c[2]],{radius:16+Math.sqrt(intensity)*28,color:'#ef6b37',weight:2,fillColor:'#f48b37',fillOpacity:.13+intensity*.4,interactive:false});circle.addTo(heatLayer)}}
function marketIssues(list){
 const root=$('nb-market-issues');if(!root)return;
 const now=Date.now();
 const event=/(?:실적|어닝|매출|영업이익|순이익|주가|증시|주식|급등|급락|폭락|상장폐지|인수합병|기업\\s*인수|기업\\s*합병|금리\\s*(?:인상|인하|동결)|earnings|revenue|profit|shares?|stocks?|stock market|stock exchange|nasdaq|s&p 500|dow jones|ipo|merger|acquisition|takeover|delisting|rate\\s*(?:cut|hike))/i;
 const noise=/(?:광고|홍보|협찬|쇼핑|할인|스포츠|연예|sponsored|advertorial|promotion|shopping|celebrity|soccer)/i;
 const rows=list.filter(a=>{const t=String(a.title||'')+' '+String(a.title_ko||'');const d=validDate(a);return d&&d.getTime()<=now+3600000&&d.getTime()>=now-7*86400000&&event.test(t)&&!noise.test(t);})
  .sort((a,b)=>validDate(b)-validDate(a));
 const seen=new Set(),picked=[];
 for(const a of rows){const key=nbPriorityKey(a);if(seen.has(key))continue;seen.add(key);picked.push(a);if(picked.length>=5)break;}
 root.innerHTML=picked.length?picked.map(a=>'<div class="nb2-row"><span class="nb2-tag">📈 '+(lang==='ko'?'증시·기업':'Markets')+'</span><a target="_blank" rel="noopener noreferrer" href="'+safe(String(a.url||'').startsWith('https://')||String(a.url||'').startsWith('http://')?a.url:'#')+'">'+safe(window.NBTitleTranslation?.title(a)||(a.title_ko||a.title))+'</a></div>').join(''):'<p class="nb2-muted">'+(lang==='ko'?'최근 7일간 수집된 주요 증시·기업 뉴스가 없습니다.':'No qualifying market news in the past 7 days.')+'</p>';
}
function riskSignals(list){
 const root=$('nb-risk-signals');if(!root)return;
 const groups=[
  {label:'⚔️ 군사·안보',re:/(?:전쟁|교전|공습|미사일\\s*발사|무력\\s*충돌|군사\\s*공격|침공|war|airstrike|missile launch|armed conflict|invasion|military attack)/i},
  {label:'🦠 감염병',re:/(?:감염병|전염병|집단\\s*감염|확진자\\s*급증|팬데믹|outbreak|epidemic|pandemic|disease spread)/i},
  {label:'📉 금융·경제',re:/(?:증시\\s*(?:폭락|급락)|주가\\s*(?:폭락|급락)|금융\\s*(?:위기|제재)|국가\\s*부도|은행\\s*파산|기업\\s*파산|관세\\s*(?:충격|폭탄|인상|위협)|금리\\s*(?:급등|급락|급변)|stock market (?:crash|plunge|selloff)|stocks? (?:plunge|tumble|crash)|shares? (?:plunge|tumble|crash)|financial crisis|financial sanctions|sovereign default|bank (?:collapse|failure)|bankruptcy|tariff (?:shock|hike|threat)|threatens? to (?:double|raise|impose) tariffs?|interest rate (?:shock|surge|plunge))/i},
  {label:'🌋 재난·기후',re:/(?:대형\\s*지진|강진|대홍수|산불\\s*확산|초강력\\s*태풍|earthquake|major flood|wildfire|super typhoon|hurricane)/i}
 ];
 const now=Date.now(),day=86400000;
 const dated=list.map(a=>({a,d:validDate(a),t:String(a.title||'')+' '+String(a.title_ko||'')})).filter(x=>x.d&&x.d.getTime()<=now+3600000&&x.d.getTime()>=now-8*day);
 const html=groups.map(g=>{
  const matches=dated.filter(x=>g.re.test(x.t)),recent=matches.filter(x=>x.d.getTime()>=now-day),prior=matches.filter(x=>x.d.getTime()<now-day);
  const base=prior.length/7,ratio=base?recent.length/base:null;
  const trend=recent.length>=3&&ratio!==null&&ratio>=2?'보도 급증':recent.length?'관련 보도 있음':'최근 24시간 보도 없음';
  const seen=new Set(),articles=[];
  for(const x of recent.sort((a,b)=>b.d-a.d)){const k=nbPriorityKey(x.a);if(seen.has(k))continue;seen.add(k);articles.push(x.a);if(articles.length>=5)break;}
  const links=articles.map(a=>'<div class="nb2-row"><a target="_blank" rel="noopener noreferrer" href="'+safe(String(a.url||'').startsWith('https://')||String(a.url||'').startsWith('http://')?a.url:'#')+'">'+safe(window.NBTitleTranslation?.title(a)||(a.title_ko||a.title))+'</a></div>').join('');
  return '<details class="nb-risk-group"><summary><strong>'+g.label+'</strong> · '+trend+'</summary>'+ (links||'<p class="nb2-muted">최근 24시간 관련 기사가 없습니다.</p>')+'</details>';
 }).join('');
 root.innerHTML='<p class="nb2-muted">수집 기사 제목 기준 자동 분류 · 보도량은 실제 위험도를 의미하지 않습니다.</p>'+html;
}
function afterRender(list,all){lastList=list;lastAll=all;bio(list);alerts(list);marketIssues(list);riskSignals(all?.length?all:list);saveButtons();if(showSaved)saved()}
function translate(){document.querySelectorAll('[data-nb]').forEach(el=>{el.textContent=tr(el.dataset.nb)});$('nb-lang').textContent=lang==='ko'?'EN':'한국어';$('nb-clear').textContent=tr('clear');const sel=$('nb-date');if(sel){[...sel.options].forEach(o=>{const key=({'1':'hours','3':'days3','7':'days7','30':'days30','all':'all'})[o.value];if(key)o.textContent=tr(key)})}$('nb-notice').textContent=tr('notice');document.documentElement.lang=lang;afterRender(lastList,lastAll)}
window.NB2={dateOK,heatmap,afterRender};
$('nb-date').addEventListener('change',()=>{document.getElementById('nb-tour-toggle')?.checked&&document.getElementById('nb-tour-toggle').click();render()});$('nb-from')?.addEventListener('change',()=>render());$('nb-to')?.addEventListener('change',()=>render());$('nb-heat')?.addEventListener('change',()=>render());$('nb-clear').addEventListener('click',()=>{$('nb-date').value='all';if($('nb-from'))$('nb-from').value='';if($('nb-to'))$('nb-to').value='';render()});
$('nb-lang').addEventListener('click',()=>{lang=lang==='ko'?'en':'ko';write('nb2-language',lang);translate()});$('nb-bookmark-open').addEventListener('click',()=>{$('nb-bookmarks')?.scrollIntoView({behavior:'smooth',block:'nearest'});$('nb-scrap-search')?.focus({preventScroll:true})});
document.addEventListener('click',e=>{const btn=e.target.closest('.nb2-bookmark,.nb2-remove');if(!btn)return;const url=btn.dataset.url;if(btn.classList.contains('nb2-remove'))delete bookmarks[url];else if(bookmarks[url])delete bookmarks[url];else{const anchor=btn.previousElementSibling;const title=anchor?.querySelector('strong')?.textContent||anchor?.textContent?.trim()||url;const match=lastAll.find(a=>a.url===url)||{};const category=String(match.category||'');const folder=/스포츠|sport/i.test(category+' '+title)?'스포츠':/경제|금융|business|econom/i.test(category)?'경제':/과학|기술|science|tech/i.test(category)?'과학·기술':/외교|국제|정치|politic/i.test(category)?'국제·정치':'기타';bookmarks[url]={url,title,folder,source:match.source||match.publisher||'',savedAt:new Date().toISOString()}}write('nb2-bookmarks',bookmarks);saveButtons();syncBookmarkStars();if(showSaved)saved()});
$('nb-scrap-search')?.addEventListener('input',saved);
$('nb-scrap-folder')?.addEventListener('change',saved);
document.addEventListener('change',e=>{const el=e.target.closest('.nb-scrap-assign');if(!el)return;const a=bookmarks[el.dataset.url];if(!a)return;a.folder=el.value;write('nb2-bookmarks',bookmarks);saved()});
$('nb-scrap-export')?.addEventListener('click',scrapExport);
$('nb-scrap-import')?.addEventListener('change',async e=>{await scrapImport(e.target.files?.[0]);e.target.value=''});
$('nb-scrap-clear')?.addEventListener('click',()=>{if(!Object.keys(bookmarks).length)return;if(!confirm(lang==='ko'?'저장한 모든 스크랩을 삭제할까요? 이 작업은 되돌릴 수 없습니다.':'Delete all saved bookmarks? This cannot be undone.'))return;bookmarks={};write('nb2-bookmarks',bookmarks);syncBookmarkStars();saved()});
// Put the existing scrapbook in the former biotech dashboard column.
// Move the actual DOM node to preserve stored bookmarks and all event handlers.
(function mountScrapbook(){
 const panel=$('nb-bookmarks'),bioPanel=$('nb-bio'),columns=document.querySelector('#nb-intelligence .nb2-columns');
 if(!panel||!columns)return;
 const target=bioPanel?.closest('section')||columns.children[1];
 if(target){target.replaceWith(panel)}else{columns.appendChild(panel)}
 panel.hidden=false;
 panel.classList.add('nb-scrap-inline');
 const css=document.createElement('style');
 css.textContent=`#nb-intelligence .nb2-columns{align-items:stretch}#nb-intelligence .nb2-columns>section{height:310px;max-height:310px;min-height:0;box-sizing:border-box;display:flex;flex-direction:column;overflow:hidden}#nb-intelligence .nb2-columns>section:first-child #nb-alerts{flex:1;min-height:0;overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin}#nb-intelligence #nb-bookmarks.nb-scrap-inline{min-width:0;margin:0;padding:12px 14px;border:1px solid var(--border,#334155);border-radius:7px}#nb-intelligence #nb-bookmarks.nb-scrap-inline #nb-saved-list{grid-template-columns:minmax(0,1fr);flex:1;min-height:0;max-height:none;overflow-y:auto;overscroll-behavior:contain;scrollbar-width:thin}#nb-intelligence #nb-bookmarks.nb-scrap-inline .nb-scrap-toolbar{min-width:0}#nb-intelligence #nb-bookmarks.nb-scrap-inline .nb-scrap-toolbar>*{max-width:100%}@media(max-width:780px){#nb-intelligence .nb2-columns{grid-template-columns:minmax(0,1fr)!important}}`;
 document.head.appendChild(css);
})();
translate();
})();
