const BIO_CATEGORIES=['제약·신약','미생물','의료기기','바이오기업','감염병'];
const norm=s=>String(s??'').normalize('NFKC').trim().replace(/\s+/g,'').toLocaleLowerCase();
const normText=s=>String(s??'').normalize('NFKC').toLocaleLowerCase();
const aliasMatch=(text,alias)=>{
 const k=normText(alias).trim();if(!k)return false;
 if(/^[a-z][a-z .'-]*$/.test(k)){
  const escaped=k.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  return new RegExp(`(^|[^a-z])${escaped}(?=$|[^a-z])`,'i').test(text);
 }
 return text.includes(k);
};

const map=L.map('map',{worldCopyJump:true,minZoom:2,maxZoom:7,zoomControl:true}).setView([22,15],2);
const nbBaseTiles=L.tileLayer(
 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',{
 attribution:'Tiles &copy; Esri',
 maxNativeZoom:16,maxZoom:19
}).addTo(map);

const nbMapThemeStyle=document.createElement('style');
nbMapThemeStyle.textContent=`
 #map.nb-map-dark .leaflet-tile-pane {filter:invert(1) hue-rotate(180deg) brightness(.76) contrast(.9)}
 #map .leaflet-tile-pane {transition:filter .25s ease}
`;
document.head.appendChild(nbMapThemeStyle);

function nbSetMapTheme(dark){
 const el=map.getContainer();
 el.classList.toggle('nb-map-dark',!!dark);
}
window.NEXTBIO_setMapTheme=nbSetMapTheme;
nbSetMapTheme(document.body.classList.contains('dark-mode') ||
 document.documentElement.classList.contains('theme-preload-dark'));

const layer=L.layerGroup().addTo(map);
let all=[],chosen=null,onlyUnclassified=false;

function ensureUnclassifiedButton(){
 const subtitle=$('country-subtitle');
 if(!subtitle||$('unclassified-toggle'))return;
 const btn=document.createElement('button');
 btn.id='unclassified-toggle';
 btn.type='button';
 btn.style.cssText='display:inline-block;margin:8px 0;padding:8px 13px;border-radius:8px;border:1px solid #64748b;background:#0f172a;color:white;cursor:pointer';
 btn.addEventListener('click',()=>{
  stopTour();
  chosen=null;
  onlyUnclassified=!onlyUnclassified;
  render();
 });
 subtitle.insertAdjacentElement('afterend',btn);
}

const nbExtraPlaces={
 '미국':['ohio','오하이오','anchorage','앵커리지','alaska','알래스카','florida','플로리다','georgia state','atlanta','애틀랜타','pennsylvania','펜실베이니아','philadelphia','필라델피아','virginia','버지니아','west virginia','웨스트버지니아','maryland','메릴랜드','massachusetts','매사추세츠','connecticut','코네티컷','new jersey','뉴저지','new mexico','뉴멕시코','arizona','애리조나','nevada','네바다','oregon','오리건','워싱턴주','washington state','seattle','시애틀','colorado','콜로라도','denver','덴버','michigan','미시간','detroit','디트로이트','illinois','일리노이','wisconsin','위스콘신','minnesota','미네소타','iowa','아이오와','indiana','인디애나','kentucky','켄터키','tennessee','테네시','nashville','내슈빌','missouri','미주리','kansas','캔자스','oklahoma','오클라호마','arkansas','아칸소','louisiana','루이지애나','new orleans','뉴올리언스','mississippi','미시시피','alabama','앨라배마','south carolina','사우스캐롤라이나','north carolina','노스캐롤라이나','north dakota','노스다코타','south dakota','사우스다코타','nebraska','네브래스카','montana','몬태나','wyoming','와이오밍','idaho','아이다호','utah','유타','hawaii','하와이','maine','메인주','vermont','버몬트','new hampshire','뉴햄프셔','rhode island','로드아일랜드','delaware','델라웨어','san francisco','샌프란시스코','san diego','샌디에이고','houston','휴스턴','dallas','댈러스','miami','마이애미','baltimore','볼티모어','cleveland','클리블랜드','columbus ohio','콜럼버스','cdc atlanta'],
 '대한민국':['경기도','경북','경남','경상북도','경상남도','전라남도','전라북도','전남','전북','충청남도','충청북도','충남','충북','강원도','강원특별자치도','세종시','세종특별자치시','제주도','제주특별자치도','화성시','동탄','용인','성남','안양','안산','평택','천안','청주','전주','목포','여수','포항','창원','진주','김해','춘천','원주','강릉','군산','순천'],
 '인도':['andhra pradesh','안드라프라데시','maharashtra','마하라슈트라','karnataka','카르나타카','kerala','케랄라','tamil nadu','타밀나두','uttar pradesh','우타르프라데시','gujarat','구자라트','hyderabad','하이데라바드','chennai','첸나이','kolkata','콜카타','pune','푸네'],
 '영국':['belfast','벨파스트','wales','웨일스','cardiff','카디프','manchester','맨체스터','birmingham uk','리버풀','liverpool','edinburgh','에든버러','glasgow','글래스고','northern ireland','북아일랜드'],
 '중국':['guangdong','광둥','guangzhou','광저우','chengdu','청두','hangzhou','항저우','nanjing','난징','suzhou','쑤저우','쑤저우시','tianjin','톈진','chongqing','충칭','hubei','후베이','xinjiang','신장위구르','홍콩','hong kong','마카오','macau'],
 '일본':['hokkaido','홋카이도','sapporo','삿포로','fukuoka','후쿠오카','nagoya','나고야','hiroshima','히로시마','okinawa','오키나와','yokohama','요코하마'],
 '캐나다':['ontario','온타리오','quebec','퀘벡','montreal','몬트리올','alberta','앨버타','calgary','캘거리','british columbia','브리티시컬럼비아'],
 '호주':['new south wales','뉴사우스웨일스','queensland','퀸즐랜드','victoria australia','빅토리아주','perth','퍼스','brisbane','브리즈번','adelaide','애들레이드'],
 '브라질':['rio de janeiro','리우데자네이루'],
 '인도네시아':['bali','발리','surabaya','수라바야'],
 '베트남':['da nang','다낭','ho chi minh city','호치민시'],
 '우크라이나':['kharkiv','하르키우','odesa','오데사','dnipro','드니프로'],
 '러시아':['saint petersburg','st petersburg','상트페테르부르크','siberia','시베리아'],
 '콩고민주공화국':['democratic republic of congo','콩고민주공화국','킨샤사','kinshasa'],
 '아랍에미리트':['abu dhabi','아부다비'],
 '멕시코':['guadalajara','과달라하라','monterrey','몬테레이']
};

const nbPlaceMap=new Map(Object.entries(nbExtraPlaces));
const nbCountryNames=new Set(countries.map(c=>c[0]));

function nbPlaceMatches(t){
 const found=[];
 for(const [name,aliases] of nbPlaceMap){
  if(nbCountryNames.has(name)&&aliases.some(k=>aliasMatch(t,k)))found.push(name);
 }
 return found;
}

const nbCountryContextRules=[
 ['대한민국', /(?:질병관리청|질병청|식약처|식품의약품안전처|보건복지부|산업통상자원부|한국은행|한은|금융위원회|금융감독원|코스피|코스닥|국회|국민대|서울대|연세대|고려대|카이스트|KAIST|K-바이오|국산\s*신약|국내\s*(?:제약|바이오|의료|기업|연구|증시)|전국\s*(?:병원체|감시기관)|[가-힣]+시(?:청|의회)|[가-힣]+도청|한미약품|SK바이오팜|대웅제약|안국약품|GC녹십자|지씨씨엘|셀트리온|삼성바이오로직스|유한양행|종근당|보령제약|동아에스티|디앤디파마텍|뉴릭스|한국\s*제약)/i],
 ['미국', /(?:\b(?:FDA|NIH|CDC|HHS|DHS|USDA|SEC|NASDAQ|NYSE|US\s+measles|U\.S\.\s+measles)\b|미\s*중간선거|미국\s*식품의약국|미\s*증시|미\s*연준|연방준비제도)/i],
 ['영국', /\b(?:NHS|MHRA|UKHSA)\b/i],
 ['유럽연합', /\b(?:EMA|ECDC)\b/i]
];

const nbCountryContextValid=nbCountryContextRules.filter(
 ([name])=>countries.some(c=>c[0]===name)
);

function nbContextMatches(a){
 const t=[a.title,a.summary].filter(Boolean).join(' ');
 return nbCountryContextValid
  .filter(([,rx])=>rx.test(t))
  .map(([name])=>name);
}

function matchedCountries(a){
 const explicit=Array.isArray(a.countries)
  ?a.countries.filter(n=>nbCountryNames.has(n))
  :[];

 if(explicit.length)return [...new Set(explicit)];

 const headline=normText(a.title||'');
 const summary=normText(a.summary||'');

 const match=t=>countries
  .filter(c=>c[3].some(k=>aliasMatch(t,k)))
  .map(c=>c[0])
  .filter(n=>
   !(n==='인도'&&/인도네시아/.test(t))&&
   !(n==='수단'&&/남수단/.test(t))&&
   !(n==='콩고공화국'&&/콩고민주공화국/.test(t))
  );

 const titleMatches=[...new Set([
  ...match(headline),
  ...nbPlaceMatches(headline)
 ])];

 if(titleMatches.length)return titleMatches;

 const context=nbContextMatches(a);
 if(context.length)return [...new Set(context)];

 return [...new Set([
  ...match(summary),
  ...nbPlaceMatches(summary)
 ])];
}

function filtered(){
 const category=$('category')?.value||'전체';
 const query=($('search')?.value||'').trim().toLocaleLowerCase();
 const region=$('region-filter')?.value||'전체';
 const sub=$('micro-filter')?.value||'전체';

 return all.filter(a=>{
  const cat=norm(a.category);
  const selected=norm(category);

  const catOK=category==='전체'||cat===selected||
   (category==='바이오'&&
    (cat===norm('바이오')||BIO_CATEGORIES.some(c=>norm(c)===cat)));

  const regionOK=region==='전체'||a.region===region;
  const subOK=sub==='전체'||a.subcategory===sub;

  const queryOK=!query||[
   a.title,a.title_ko,a.summary,a.source,
   a.category,a.subcategory,...(a.countries||[])
  ].join(' ').toLocaleLowerCase().includes(query);

  const dateOK=window.NB2?.dateOK?.(a)??true;

  return catOK&&regionOK&&subOK&&queryOK&&dateOK;
 });
}

function item(a,cls){
 const url=String(a.url||'');
 const href=/^https?:\/\//i.test(url)?safe(url):'#';

 return `<a class="${cls}" href="${href}" target="_blank" rel="noopener noreferrer"><span class="category">${safe(a.category||'일반')}</span><strong>${safe(a.title||'제목 없음')}</strong>${cls==='latest-item'?`<p>${safe(a.summary||'').slice(0,150)}</p>`:''}<span class="meta">${safe(a.region||'')} ${safe(a.subcategory||'')} · ${safe(a.source||'원문')} · ${dateText(a.published)}</span></a>`;
}

/* 국가 자동 순회 */
let tourTimer=null,tourIndex=0,tourCountries=[];
const tourToggle=$('nb-tour-toggle');
const tourStatus=$('nb-tour-status');

function stopTour(message='자동 순회 꺼짐'){
 if(tourTimer!==null){
  clearInterval(tourTimer);
  tourTimer=null;
 }
 if(tourToggle)tourToggle.checked=false;
 if(tourStatus)tourStatus.textContent=message;
}

function tourTargets(){
 const list=filtered(),seen=new Set(),result=[];

 for(const a of list){
  for(const name of a.countries||[]){
   if(seen.has(name))continue;
   if(!countries.some(c=>c[0]===name))continue;

   seen.add(name);
   result.push(name);

   if(result.length>=12)return result;
  }
 }
 return result;
}

function tourStep(){
 if(document.hidden)return;

 if(!tourCountries.length){
  stopTour('순회할 국가가 없습니다');
  return;
 }

 const name=tourCountries[tourIndex%tourCountries.length];
 tourIndex++;
 chosen=name;
 onlyUnclassified=false;
 render();

 const c=countries.find(x=>x[0]===name);
 if(c)map.flyTo([c[1],c[2]],4,{duration:1.3});

 if(tourStatus){
  tourStatus.textContent=`${name} · ${((tourIndex-1)%tourCountries.length)+1}/${tourCountries.length}`;
 }
}

function startTour(){
 stopTour();
 tourCountries=tourTargets();
 tourIndex=0;

 if(!tourCountries.length){
  stopTour('현재 조건에 순회할 국가가 없습니다');
  return;
 }

 if(tourToggle)tourToggle.checked=true;
 tourStep();
 tourTimer=setInterval(tourStep,9000);
}

tourToggle?.addEventListener('change',()=>{
 if(tourToggle.checked)startTour();
 else stopTour();
});

map.on('dragstart',()=>{
 if(tourTimer!==null){
  stopTour('수동 탐색 중 · 자동 순회 꺼짐');
 }
});

function selectCountry(name){
 if(tourTimer!==null){
  stopTour('국가 선택 · 자동 순회 꺼짐');
 }

 chosen=name;
 onlyUnclassified=false;
 render();

 const c=countries.find(x=>x[0]===name);
 if(c){
  map.flyTo(
   [c[1],c[2]],
   Math.max(map.getZoom(),4),
   {duration:.6}
  );
 }
}

/* 최신 뉴스 10개씩 페이지 넘기기 */
const NB_PAGE_SIZE=10;
let nbNewsPage=1,nbNewsSignature='';

const nbPagerStyle=document.createElement('style');
nbPagerStyle.textContent=`
 #nb-news-pagination{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:7px;padding:22px 10px 30px}
 #nb-news-pagination button{min-width:36px;padding:9px 12px;border:1px solid #64748b;border-radius:7px;background:transparent;color:inherit;font:inherit;cursor:pointer}
 #nb-news-pagination button[aria-current="page"]{background:#2563eb;color:#fff;border-color:#2563eb;font-weight:700}
 #nb-news-pagination button:disabled{opacity:.35;cursor:default}
 #nb-news-pagination button:focus-visible{outline:2px solid #60a5fa;outline-offset:2px}
 #nb-news-pagination .nb-page-summary{flex-basis:100%;text-align:center;font-size:12px;opacity:.75;margin-top:5px}
`;
document.head.appendChild(nbPagerStyle);

function nbRenderLatestPage(list){
 const feed=$('latest-list');
 if(!feed)return;

 const pages=Math.max(1,Math.ceil(list.length/NB_PAGE_SIZE));
 nbNewsPage=Math.min(Math.max(1,nbNewsPage),pages);
 const start=(nbNewsPage-1)*NB_PAGE_SIZE;

 feed.innerHTML=list.length
  ?list.slice(start,start+NB_PAGE_SIZE)
   .map(a=>item(a,'latest-item')).join('')
  :'<p class="empty">표시할 기사가 없습니다.</p>';

 let pager=$('nb-news-pagination');

 if(!pager){
  pager=document.createElement('nav');
  pager.id='nb-news-pagination';
  pager.setAttribute('aria-label','최신 뉴스 페이지');
  feed.insertAdjacentElement('afterend',pager);
 }

 if(pages<=1){
  pager.hidden=true;
  pager.innerHTML='';
  return;
 }

 pager.hidden=false;
 const pageButtons=[];
 const first=Math.max(1,Math.min(nbNewsPage-2,pages-4));
 const last=Math.min(pages,first+4);

 for(let p=first;p<=last;p++){
  pageButtons.push(
   `<button type="button" data-page="${p}" ${p===nbNewsPage?'aria-current="page"':''} aria-label="${p}페이지">${p}</button>`
  );
 }

 pager.innerHTML=
  `<button type="button" data-page="${nbNewsPage-1}" ${nbNewsPage===1?'disabled':''}>이전</button>`+
  pageButtons.join('')+
  `<button type="button" data-page="${nbNewsPage+1}" ${nbNewsPage===pages?'disabled':''}>다음</button>`+
  `<span class="nb-page-summary">전체 ${list.length}건 · ${nbNewsPage} / ${pages} 페이지</span>`;
}

document.addEventListener('click',e=>{
 const btn=e.target.closest('#nb-news-pagination button[data-page]');
 if(!btn||btn.disabled)return;

 const next=Number(btn.dataset.page);
 if(!Number.isInteger(next)||next===nbNewsPage)return;

 nbNewsPage=next;
 const list=filtered();

 nbRenderLatestPage(list);
 window.NB2?.afterRender?.(list,all);

 $('latest-list')?.scrollIntoView({
  behavior:'smooth',
  block:'start'
 });
});

/* 지도 및 뉴스 목록 렌더링 */
function render(){
 const list=filtered(),groups=new Map();

 const signature=list.map(a=>a.url).join('\n');
 if(signature!==nbNewsSignature){
  nbNewsPage=1;
  nbNewsSignature=signature;
 }

 for(const a of list){
  for(const name of a.countries){
   if(!groups.has(name))groups.set(name,[]);
   groups.get(name).push(a);
  }
 }

 const unclassified=list.filter(a=>!a.countries.length);

 layer.clearLayers();
 window.NB2?.heatmap?.(groups);

 for(const c of countries){
  const articles=groups.get(c[0]);
  if(!articles?.length)continue;

  const icon=L.divIcon({
   className:'',
   html:`<div class="news-pin ${chosen===c[0]?'selected':''}">${articles.length}</div>`,
   iconSize:[30,30],
   iconAnchor:[15,15]
  });

  const marker=L.marker([c[1],c[2]],{
   icon,
   title:`${c[0]} 관련 기사 ${articles.length}건`
  }).addTo(layer);

  marker.on('click',()=>selectCountry(c[0]));
  marker.bindTooltip(`${c[0]} · ${articles.length}건`);
 }

 if($('stat-articles')){
  $('stat-articles').textContent=all.length;
 }

 if($('stat-countries')){
  $('stat-countries').textContent=groups.size;
 }

 const selected=onlyUnclassified
  ?unclassified
  :(chosen?(groups.get(chosen)||[]):list);

 if($('country-title')){
  $('country-title').textContent=onlyUnclassified
   ?'국가 미분류 뉴스'
   :(chosen?`${chosen} 관련 뉴스`:'전 세계 주요 뉴스');
 }

 if($('country-subtitle')){
  $('country-subtitle').textContent=onlyUnclassified
   ?`국가 정보가 확인되지 않은 기사 ${selected.length}건`
   :(chosen
    ?`${chosen} 관련 기사 ${selected.length}건 · 전체 목록 표시`
    :`현재 필터 ${list.length}건 · 국가 분류 ${list.length-unclassified.length}건 · 국가 미분류 ${unclassified.length}건 · 지도 마커 ${groups.size}개`);
 }

 ensureUnclassifiedButton();

 const toggle=$('unclassified-toggle');
 if(toggle){
  toggle.textContent=onlyUnclassified
   ?'전체 뉴스 보기'
   :`국가 미분류 뉴스 보기 (${unclassified.length}건)`;
 }

 if($('country-feed')){
  $('country-feed').innerHTML=selected.length
   ?selected.map(a=>item(a,'country-item')).join('')
   :'<p class="empty">선택한 조건에 해당하는 뉴스가 없습니다.</p>';
 }

 if($('count')){
  $('count').textContent=`${list.length} ARTICLES`;
 }

 nbRenderLatestPage(list);

 if($('ticker')){
  $('ticker').textContent=list[0]?.title||
   '현재 필터에 해당하는 뉴스가 없습니다.';
 }

 window.NB2?.afterRender?.(list,all);
}

/* 필터 이벤트 */
$('category')?.addEventListener('change',()=>{
 stopTour();
 chosen=null;
 onlyUnclassified=false;

 const m=$('micro-filter');
 if(m){
  m.style.display=$('category').value==='미생물'
   ?'inline-block':'none';
  m.value='전체';
 }
 render();
});

$('search')?.addEventListener('input',()=>{
 stopTour();
 chosen=null;
 onlyUnclassified=false;
 render();
});

$('region-filter')?.addEventListener('change',()=>{
 stopTour();
 chosen=null;
 onlyUnclassified=false;
 render();
});

$('micro-filter')?.addEventListener('change',()=>{
 stopTour();
 chosen=null;
 onlyUnclassified=false;
 render();
});

$('reset')?.addEventListener('click',()=>{
 stopTour();
 chosen=null;
 onlyUnclassified=false;

 if($('category'))$('category').value='전체';
 if($('search'))$('search').value='';
 if($('region-filter'))$('region-filter').value='전체';

 if($('micro-filter')){
  $('micro-filter').value='전체';
  $('micro-filter').style.display='none';
 }

 map.setView([22,15],2);
 render();
});

if($('today')){
 $('today').textContent=new Date().toLocaleDateString(
  'ko-KR',{
   year:'numeric',
   month:'long',
   day:'numeric'
  }
 );
}

window.addEventListener('resize',()=>map.invalidateSize());

/* 뉴스 데이터 불러오기 */
(async()=>{
 try{
  const r=await fetch(DATA_URL+'?t='+Date.now(),{
   cache:'no-store'
  });

  if(!r.ok)throw Error(`HTTP ${r.status}`);

  const data=await r.json();

  all=(Array.isArray(data.articles)?data.articles:[])
   .filter(a=>
    a&&a.title&&/^https?:\/\//i.test(a.url||'')
   )
   .map(a=>({
    ...a,
    countries:matchedCountries(a)
   }))
   .sort((a,b)=>
    new Date(b.published)-new Date(a.published)
   );

  if($('updated')){
   $('updated').textContent=data.updated
    ?`업데이트 ${dateText(data.updated)}`
    :'업데이트 정보 없음';
  }

  render();

  setTimeout(()=>map.invalidateSize(),200);
  setTimeout(()=>{
   if(tourToggle)startTour();
  },1400);

 }catch(e){
  if($('ticker')){
   $('ticker').textContent='뉴스 데이터를 불러오지 못했습니다.';
  }

  if($('country-feed')){
   $('country-feed').innerHTML=
    '<p class="empty">data/articles.json 파일과 뉴스 수집 작업을 확인하세요.</p>';
  }

  if($('latest-list')){
   $('latest-list').innerHTML=
    '<p class="empty">뉴스 데이터 로딩 실패: '+
    safe(e.message)+'</p>';
  }

  console.error(e);
 }
})();
