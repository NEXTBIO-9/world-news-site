/* NEXT BIO 2.0: non-destructive extension of existing app.js */
(function(){
'use strict';
const $=id=>document.getElementById(id);
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const read=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key))??fallback}catch{return fallback}};
const write=(key,val)=>{try{localStorage.setItem(key,JSON.stringify(val))}catch{}};
let bookmarks=read('nb2-bookmarks',{}),lang=read('nb2-language','ko'),showSaved=false,lastList=[],lastAll=[];
const labels={ko:{saved:'북마크',period:'기간',from:'시작일',to:'종료일',heat:'뉴스 밀도 지도',alerts:'신규·주요 뉴스',bio:'바이오 대시보드',empty:'표시할 뉴스가 없습니다.',clear:'초기화',all:'전체 기간',hours:'최근 24시간',days3:'최근 3일',days7:'최근 7일',days30:'최근 30일',notice:'속보 표시는 수집된 기사 제목과 시간에 기반한 자동 분류이며, 공식 긴급재난 알림이 아닙니다.'},en:{saved:'Bookmarks',period:'Period',from:'From',to:'To',heat:'News density overlay',alerts:'New & important stories',bio:'Biotech dashboard',empty:'No matching articles.',clear:'Reset',all:'All dates',hours:'Last 24 hours',days3:'Last 3 days',days7:'Last 7 days',days30:'Last 30 days',notice:'Breaking labels are automated based on article timestamps and headlines, not official emergency alerts.'}};
const tr=k=>labels[lang]?.[k]||labels.ko[k]||k;
const validDate=a=>{const d=new Date(a.published);return Number.isFinite(d.getTime())?d:null};
function dateOK(a){const d=validDate(a);if(!d)return false;const period=Number($('nb-date')?.value||7);const now=Date.now();return d.getTime()>=now-period*86400000&&d.getTime()<=now+3600000}
function bio(list){const cats=['미생물','제약·신약','의료기기','바이오기업','감염병'];const counts=cats.map(k=>[k,list.filter(a=>a.category===k).length]);const max=Math.max(1,...counts.map(x=>x[1]));$('nb-bio').innerHTML=counts.map(([k,n])=>`<div class="nb2-row">${safe(k)} <span class="nb2-bar" style="width:${Math.round(n/max*42)}%"></span><b>${n}</b></div>`).join('')}
/* Importance scoring applies ONLY to the "New & important" panel.
   Other feeds, country markers, and category filters are unchanged. */
const nbPriorityRules=[
 {points:85,re:/(?:전쟁\s*(?:발발|선포|확전)|침공|대규모\s*(?:공습|폭격|공격)|핵(?:공격|위협)|선전포고|invasion|war\s+(?:breaks?\s+out|declared|escalat)|mass(?:ive)?\s+(?:airstrike|bombing|attack)|nuclear\s+(?:strike|threat))/i},
 {points:80,re:/(?:팬데믹|세계보건기구.{0,25}(?:비상|경보)|국제적\s*공중보건\s*비상|신종\s*(?:감염병|바이러스).{0,25}(?:확산|발생)|pandemic|public\s+health\s+emergency|who\s+declares?.{0,30}emergency|novel\s+(?:virus|pathogen).{0,30}(?:outbreak|spread))/i},
 {points:76,re:/(?:규모\s*[6-9](?:\.[0-9])?\s*지진|대지진|초강력\s*태풍|대형\s*(?:산불|홍수|재난)|수백\s*명\s*사망|earthquake.{0,30}magnitude\s*[6-9]|magnitude\s*[6-9].{0,30}earthquake|major\s+(?:earthquake|flood|wildfire)|catastrophic|hundreds\s+(?:dead|killed))/i},
 {points:72,re:/(?:국가비상사태|계엄령|국경\s*봉쇄|외교관계\s*단절|경제\s*제재|금융\s*위기|은행\s*파산|기준금리\s*(?:인상|인하)|긴급\s*금리|state\s+of\s+emergency|martial\s+law|border\s+closure|diplomatic\s+ties\s+severed|economic\s+sanctions|financial\s+crisis|bank\s+collapse|central\s+bank.{0,30}(?:rate\s+(?:cut|hike)|emergency))/i},
 {points:68,re:/(?:군사\s*충돌|미사일\s*발사|무력\s*충돌|휴전\s*붕괴|대규모\s*시위|국가\s*간\s*긴장|military\s+clash|missile\s+launch|armed\s+conflict|ceasefire\s+collapse|mass\s+protests|geopolitical\s+tensions)/i},
 {points:65,re:/(?:집단\s*감염|감염병\s*확산|확진자\s*급증|에볼라\s*확산|콜레라\s*확산|감염병\s*비상|outbreak.{0,35}(?:spreads?|surges?|deaths?|emergency)|surge\s+in\s+(?:cases|infections)|ebola\s+outbreak|cholera\s+outbreak)/i}
];
const nbPriorityContext=/(?:전쟁|군사|분쟁|미사일|공습|폭격|외교|제재|관세|금리|중앙은행|금융|경제위기|지진|태풍|홍수|산불|재난|감염병|에볼라|콜레라|전염병|확진|pandemic|outbreak|military|war|missile|airstrike|sanctions|central bank|financial crisis|earthquake|typhoon|flood|wildfire|ebola|cholera)/i;
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
function alerts(list){
 const now=Date.now(),threshold=70;
 const ranked=list.map(a=>({a,score:nbPriorityScore(a),date:validDate(a)}))
  .filter(x=>x.date&&x.date.getTime()>=now-48*3600000&&x.date.getTime()<=now+3600000&&x.score>=threshold)
  .sort((x,y)=>y.score-x.score||y.date-x.date);
 const seen=new Set(),chosen=[];
 for(const x of ranked){const key=nbPriorityKey(x.a);if(seen.has(key))continue;seen.add(key);chosen.push(x);if(chosen.length>=5)break;}
 const root=$('nb-alerts');if(!root)return;
 root.innerHTML=chosen.length?chosen.map(({a,score})=>`<div class="nb2-row"><span class="nb2-tag">${score>=85?'🚨 ': '⚡ '}${lang==='ko'?(score>=85?'긴급':'주요'):(score>=85?'Urgent':'Priority')} · ${score}</span><a target="_blank" rel="noopener noreferrer" href="${safe(/^https?:\/\//i.test(a.url||'')?a.url:'#')}">${safe(lang==='en'?(a.title||a.title_ko):(a.title_ko||a.title))}</a></div>`).join(''):`<p class="nb2-muted">${lang==='ko'?'현재 기준에 해당하는 주요 뉴스가 없습니다.':'No qualifying priority stories right now.'}</p>`;
}
function saveButtons(){document.querySelectorAll('#latest-list a.latest-item,#country-feed a.country-item').forEach(a=>{if(a.nextElementSibling?.classList.contains('nb2-bookmark'))return;const url=a.getAttribute('href');if(!/^https?:\/\//i.test(url||''))return;const btn=document.createElement('button');btn.type='button';btn.className='nb2-bookmark';btn.dataset.url=url;btn.textContent=bookmarks[url]?'★':'☆';btn.title=tr('saved');btn.setAttribute('aria-label',tr('saved'));btn.setAttribute('aria-pressed',String(!!bookmarks[url]));const wrap=document.createElement('div');wrap.className='nb-news-row';a.parentNode.insertBefore(wrap,a);wrap.appendChild(a);wrap.appendChild(btn)})}
function saved(){const vals=Object.values(bookmarks);$('nb-saved-list').innerHTML=vals.length?vals.map(a=>`<div class="nb2-savewrap"><a href="${safe(a.url)}" target="_blank" rel="noopener noreferrer">${safe(a.title)}</a><button type="button" class="nb2-remove" data-url="${safe(a.url)}">${lang==='ko'?'삭제':'Remove'}</button></div>`).join(''):`<p class="nb2-muted">${tr('empty')}</p>`}
function afterRender(list,all){lastList=list;lastAll=all;bio(list);alerts(list);saveButtons();if(showSaved)saved()}
function translate(){document.querySelectorAll('[data-nb]').forEach(el=>{el.textContent=tr(el.dataset.nb)});$('nb-lang').textContent=lang==='ko'?'EN':'한국어';$('nb-clear').textContent=tr('clear');const sel=$('nb-date');['days7','days3','hours'].forEach((k,i)=>{sel.options[i].textContent=tr(k)});$('nb-notice').textContent=tr('notice');document.documentElement.lang=lang;afterRender(lastList,lastAll)}
window.NB2={dateOK,afterRender};
$('nb-date').addEventListener('change',()=>{if(document.getElementById('nb-tour-toggle')?.checked)document.getElementById('nb-tour-toggle').click();render()});$('nb-clear').addEventListener('click',()=>{$('nb-date').value='7';render()});
$('nb-lang').addEventListener('click',()=>{lang=lang==='ko'?'en':'ko';write('nb2-language',lang);translate()});$('nb-bookmark-open').addEventListener('click',()=>{showSaved=!showSaved;$('nb-bookmarks').hidden=!showSaved;if(showSaved)saved()});
document.addEventListener('click',e=>{const btn=e.target.closest('.nb2-bookmark,.nb2-remove');if(!btn)return;const url=btn.dataset.url;if(btn.classList.contains('nb2-remove'))delete bookmarks[url];else if(bookmarks[url])delete bookmarks[url];else{const anchor=btn.previousElementSibling;bookmarks[url]={url,title:anchor?.querySelector('strong')?.textContent||anchor?.textContent?.trim()||url}}write('nb2-bookmarks',bookmarks);saveButtons();document.querySelectorAll('.nb2-bookmark').forEach(b=>{b.textContent=bookmarks[b.dataset.url]?'★':'☆';b.setAttribute('aria-pressed',String(!!bookmarks[b.dataset.url]))});if(showSaved)saved()});
translate();
})();
