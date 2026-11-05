
/* WORLD NEWS V12 — global country classification */
const DATA_URL='./data/articles.json';
const $=id=>document.getElementById(id);
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateText=d=>{const v=new Date(d);return isNaN(v)?'':v.toLocaleString('ko-KR',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});};

// 국가명, 위도, 경도, 검색 키워드
const countries=[
['대한민국',36.5,127.8,['대한민국','한국','남한','south korea','republic of korea','seoul','서울','부산','인천','대전','대구','광주','울산','수원','제주']],
['북한',40.3,127.5,['북한','north korea','pyongyang','평양']],
['미국',39,-98,['미국','united states','u.s.','u.s.a.','usa','american','워싱턴','washington dc','washington d.c.','new york','뉴욕','california','캘리포니아','texas','텍사스','boston','보스턴','chicago','시카고','los angeles','로스앤젤레스','트럼프','바이든']],
['중국',35,104,['중국','china','chinese','beijing','베이징','shanghai','상하이','shenzhen','선전','wuhan','우한','시진핑']],
['일본',36,138,['일본','japan','japanese','tokyo','도쿄','osaka','오사카','kyoto','교토']],
['러시아',61,100,['러시아','russia','russian','moscow','모스크바','putin','푸틴']],
['우크라이나',49,32,['우크라이나','ukraine','ukrainian','kyiv','키이우','zelensky','젤렌스키']],
['대만',23.7,121,['대만','타이완','taiwan','taipei','타이베이']],
['영국',54,-2,['영국','united kingdom','britain','british','england','london','런던','scotland','스코틀랜드']],
['프랑스',46.5,2.2,['프랑스','france','french','paris','파리','lyon','리옹']],
['독일',51,10,['독일','germany','german','berlin','베를린','munich','뮌헨','frankfurt','프랑크푸르트']],
['이스라엘',31.5,35,['이스라엘','israel','israeli','tel aviv','텔아비브','jerusalem','예루살렘']],
['이란',32,53,['이란','iran','iranian','tehran','테헤란']],
['팔레스타인',31.9,35.2,['팔레스타인','palestine','palestinian','gaza','가자','west bank','서안지구']],
['사우디아라비아',24,45,['사우디','saudi arabia','saudi','riyadh','리야드']],
['인도',22,79,['인도','india','indian','new delhi','뉴델리','mumbai','뭄바이','bengaluru','벵갈루루']],
['파키스탄',30,69,['파키스탄','pakistan','pakistani','islamabad','이슬라마바드']],
['튀르키예',39,35,['튀르키예','터키','turkey','türkiye','turkiye','ankara','앙카라','istanbul','이스탄불']],
['브라질',-14,-52,['브라질','brazil','brazilian','brasilia','브라질리아','sao paulo','상파울루']],
['캐나다',56,-106,['캐나다','canada','canadian','ottawa','오타와','toronto','토론토','vancouver','밴쿠버']],
['멕시코',23,-102,['멕시코','mexico','mexican','mexico city','멕시코시티']],
['호주',-25,134,['호주','오스트레일리아','australia','australian','sydney','시드니','melbourne','멜버른','canberra','캔버라']],
['인도네시아',-2,118,['인도네시아','indonesia','indonesian','jakarta','자카르타']],
['베트남',16,108,['베트남','vietnam','vietnamese','hanoi','하노이','ho chi minh','호찌민']],
['태국',15,101,['태국','thailand','thai','bangkok','방콕']],
['필리핀',12.5,122,['필리핀','philippines','philippine','manila','마닐라']],
['이집트',27,30,['이집트','egypt','egyptian','cairo','카이로']],
['남아프리카공화국',-29,24,['남아공','남아프리카공화국','south africa','south african','cape town','케이프타운','johannesburg','요하네스버그']],
['폴란드',52,19,['폴란드','poland','polish','warsaw','바르샤바']],
['스페인',40,-4,['스페인','spain','spanish','madrid','마드리드','barcelona','바르셀로나']],
['이탈리아',42.5,12.5,['이탈리아','italy','italian','rome','로마','milan','밀라노']],
['아르헨티나',-34,-64,['아르헨티나','argentina','argentine','buenos aires','부에노스아이레스']],
['네덜란드',52.1,5.3,['네덜란드','netherlands','dutch','amsterdam','암스테르담','rotterdam','로테르담']],
['벨기에',50.5,4.5,['벨기에','belgium','belgian','brussels','브뤼셀']],
['스위스',46.8,8.2,['스위스','switzerland','swiss','zurich','취리히','geneva','제네바']],
['스웨덴',62,15,['스웨덴','sweden','swedish','stockholm','스톡홀름']],
['노르웨이',61,9,['노르웨이','norway','norwegian','oslo','오슬로']],
['덴마크',56,10,['덴마크','denmark','danish','copenhagen','코펜하겐']],
['핀란드',64,26,['핀란드','finland','finnish','helsinki','헬싱키']],
['아일랜드',53,-8,['아일랜드','ireland','irish','dublin','더블린']],
['포르투갈',39.5,-8,['포르투갈','portugal','portuguese','lisbon','리스본']],
['오스트리아',47.5,14.5,['오스트리아','austria','austrian','vienna','빈']],
['체코',49.8,15.5,['체코','czech republic','czechia','prague','프라하']],
['헝가리',47,19.5,['헝가리','hungary','hungarian','budapest','부다페스트']],
['그리스',39,22,['그리스','greece','greek','athens','아테네']],
['루마니아',45.9,24.9,['루마니아','romania','romanian','bucharest','부쿠레슈티']],
['불가리아',42.7,25.5,['불가리아','bulgaria','bulgarian','sofia','소피아']],
['세르비아',44,21,['세르비아','serbia','serbian','belgrade','베오그라드']],
['크로아티아',45.1,15.2,['크로아티아','croatia','croatian','zagreb','자그레브']],
['슬로바키아',48.7,19.7,['슬로바키아','slovakia','slovak','bratislava','브라티슬라바']],
['슬로베니아',46.1,14.8,['슬로베니아','slovenia','slovenian','ljubljana','류블랴나']],
['리투아니아',55.2,23.9,['리투아니아','lithuania','lithuanian','vilnius','빌뉴스']],
['라트비아',56.9,24.6,['라트비아','latvia','latvian','riga','리가']],
['에스토니아',58.6,25,['에스토니아','estonia','estonian','tallinn','탈린']],
['벨라루스',53.7,28,['벨라루스','belarus','belarusian','minsk','민스크']],
['몰도바',47,28.5,['몰도바','moldova','moldovan','chisinau','키시너우']],
['조지아',42,43.5,['조지아','georgia country','tbilisi','트빌리시']],
['아르메니아',40.1,45,['아르메니아','armenia','armenian','yerevan','예레반']],
['아제르바이잔',40.1,47.6,['아제르바이잔','azerbaijan','azerbaijani','baku','바쿠']],
['카자흐스탄',48,68,['카자흐스탄','kazakhstan','kazakh','astana','아스타나']],
['우즈베키스탄',41.4,64.6,['우즈베키스탄','uzbekistan','uzbek','tashkent','타슈켄트']],
['키르기스스탄',41.2,74.8,['키르기스스탄','kyrgyzstan','kyrgyz','bishkek','비슈케크']],
['타지키스탄',38.9,71,['타지키스탄','tajikistan','tajik','dushanbe','두샨베']],
['투르크메니스탄',39,59,['투르크메니스탄','turkmenistan','turkmen','ashgabat','아시가바트']],
['몽골',46.9,103.8,['몽골','mongolia','mongolian','ulaanbaatar','울란바토르']],
['네팔',28.4,84.1,['네팔','nepal','nepalese','kathmandu','카트만두']],
['방글라데시',23.7,90.4,['방글라데시','bangladesh','bangladeshi','dhaka','다카']],
['스리랑카',7.9,80.7,['스리랑카','sri lanka','sri lankan','colombo','콜롬보']],
['미얀마',21.9,95.9,['미얀마','myanmar','burma','yangon','양곤','naypyidaw','네피도']],
['캄보디아',12.6,104.9,['캄보디아','cambodia','cambodian','phnom penh','프놈펜']],
['라오스',19.8,102.5,['라오스','laos','laotian','vientiane','비엔티안']],
['말레이시아',4.2,102,['말레이시아','malaysia','malaysian','kuala lumpur','쿠알라룸푸르']],
['싱가포르',1.35,103.8,['싱가포르','singapore','singaporean']],
['브루나이',4.5,114.7,['브루나이','brunei','bandar seri begawan']],
['동티모르',-8.8,125.7,['동티모르','timor-leste','east timor','dili','딜리']],
['뉴질랜드',-41,174,['뉴질랜드','new zealand','new zealander','auckland','오클랜드','wellington','웰링턴']],
['피지',-17.7,178,['피지','fiji','fijian','suva','수바']],
['파푸아뉴기니',-6,147,['파푸아뉴기니','papua new guinea','port moresby']],
['칠레',-35,-71,['칠레','chile','chilean','santiago','산티아고']],
['페루',-10,-76,['페루','peru','peruvian','lima','리마']],
['콜롬비아',4,-74,['콜롬비아','colombia','colombian','bogota','보고타']],
['베네수엘라',7,-66,['베네수엘라','venezuela','venezuelan','caracas','카라카스']],
['에콰도르',-1.8,-78.2,['에콰도르','ecuador','ecuadorian','quito','키토']],
['볼리비아',-17,-65,['볼리비아','bolivia','bolivian','la paz','라파스']],
['파라과이',-23.4,-58.4,['파라과이','paraguay','paraguayan','asuncion','아순시온']],
['우루과이',-33,-56,['우루과이','uruguay','uruguayan','montevideo','몬테비데오']],
['쿠바',21.5,-79.5,['쿠바','cuba','cuban','havana','아바나']],
['도미니카공화국',19,-70.7,['도미니카공화국','dominican republic','santo domingo','산토도밍고']],
['아이티',19,-72.3,['아이티','haiti','haitian','port-au-prince','포르토프랭스']],
['자메이카',18.1,-77.3,['자메이카','jamaica','jamaican','kingston','킹스턴']],
['파나마',8.5,-80,['파나마','panama','panamanian','panama city']],
['코스타리카',10,-84,['코스타리카','costa rica','costa rican','san jose','산호세']],
['과테말라',15.8,-90.2,['과테말라','guatemala','guatemalan']],
['온두라스',14.8,-86.2,['온두라스','honduras','honduran','tegucigalpa']],
['엘살바도르',13.8,-88.9,['엘살바도르','el salvador','salvadoran']],
['니카라과',12.9,-85,['니카라과','nicaragua','nicaraguan','managua']],
['나이지리아',9.1,8.7,['나이지리아','nigeria','nigerian','lagos','라고스','abuja','아부자']],
['케냐',0.2,37.9,['케냐','kenya','kenyan','nairobi','나이로비']],
['에티오피아',9.1,40.5,['에티오피아','ethiopia','ethiopian','addis ababa','아디스아바바']],
['가나',7.9,-1.1,['가나','ghana','ghanaian','accra','아크라']],
['우간다',1.4,32.3,['우간다','uganda','ugandan','kampala','캄팔라']],
['탄자니아',-6.3,35,['탄자니아','tanzania','tanzanian','dar es salaam','다르에스살람']],
['르완다',-1.9,29.9,['르완다','rwanda','rwandan','kigali','키갈리']],
['콩고민주공화국',-3,23.6,['콩고민주공화국','democratic republic of the congo','dr congo','drc','kinshasa','킨샤사']],
['콩고공화국',-0.8,15.2,['콩고공화국','republic of the congo','brazzaville','브라자빌']],
['수단',15.5,30.2,['수단','sudan','sudanese','khartoum','하르툼']],
['남수단',7.3,30.5,['남수단','south sudan','juba','주바']],
['소말리아',5.2,46.2,['소말리아','somalia','somali','mogadishu','모가디슈']],
['모로코',31.8,-7.1,['모로코','morocco','moroccan','rabat','라바트','casablanca','카사블랑카']],
['알제리',28,2.6,['알제리','algeria','algerian','algiers','알제']],
['튀니지',34,9,['튀니지','tunisia','tunisian','tunis','튀니스']],
['리비아',27,17,['리비아','libya','libyan','tripoli','트리폴리']],
['세네갈',14.5,-14.5,['세네갈','senegal','senegalese','dakar','다카르']],
['코트디부아르',7.5,-5.5,['코트디부아르','ivory coast','cote d’ivoire','côte d’ivoire','abidjan','아비장']],
['카메룬',6,12,['카메룬','cameroon','cameroonian','yaounde','야운데']],
['잠비아',-13.1,27.8,['잠비아','zambia','zambian','lusaka','루사카']],
['짐바브웨',-19,29.2,['짐바브웨','zimbabwe','zimbabwean','harare','하라레']],
['모잠비크',-18.7,35.5,['모잠비크','mozambique','mozambican','maputo','마푸투']],
['마다가스카르',-19,47,['마다가스카르','madagascar','malagasy','antananarivo','안타나나리보']],
['앙골라',-12.5,18.5,['앙골라','angola','angolan','luanda','루안다']],
['보츠와나',-22,24,['보츠와나','botswana','gaborone','가보로네']],
['나미비아',-22.5,17,['나미비아','namibia','namibian','windhoek','빈트후크']],
['아랍에미리트',24,54,['아랍에미리트','united arab emirates','uae','dubai','두바이','abu dhabi','아부다비']],
['카타르',25.3,51.2,['카타르','qatar','qatari','doha','도하']],
['쿠웨이트',29.3,47.5,['쿠웨이트','kuwait','kuwaiti']],
['바레인',26,50.5,['바레인','bahrain','bahraini','manama','마나마']],
['오만',21,57,['오만','oman','omani','muscat','무스카트']],
['예멘',15.5,48,['예멘','yemen','yemeni','sanaa','사나']],
['이라크',33,44,['이라크','iraq','iraqi','baghdad','바그다드']],
['시리아',35,38,['시리아','syria','syrian','damascus','다마스쿠스']],
['요르단',31,36,['요르단','jordan','jordanian','amman','암만']],
['레바논',33.8,35.8,['레바논','lebanon','lebanese','beirut','베이루트']],
['아프가니스탄',33.9,67.7,['아프가니스탄','afghanistan','afghan','kabul','카불']],
['키프로스',35,33,['키프로스','cyprus','cypriot','nicosia','니코시아']],
['아이슬란드',65,-19,['아이슬란드','iceland','icelandic','reykjavik','레이캬비크']]
];

const BIO_CATEGORIES=['제약·신약','미생물','의료기기','바이오기업','감염병'];
const norm=s=>String(s??'').normalize('NFKC').trim().replace(/\s+/g,'').toLocaleLowerCase();
const normText=s=>String(s??'').normalize('NFKC').toLocaleLowerCase();

const aliasMatch=(text,alias)=>{
 const k=normText(alias).trim();
 if(!k)return false;
 if(/^[a-z][a-z .'-]*$/.test(k)){
  const escaped=k.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  return new RegExp(`(^|[^a-z])${escaped}(?=$|[^a-z])`,'i').test(text);
 }
 return text.includes(k);
};

const map=L.map('map',{worldCopyJump:true,minZoom:2,maxZoom:7,zoomControl:true}).setView([22,15],2);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
 attribution:'&copy; OpenStreetMap contributors',
 maxZoom:19
}).addTo(map);

const layer=L.layerGroup().addTo(map);
let all=[],chosen=null;

function matchedCountries(a){
 const explicit=Array.isArray(a.countries)
  ?a.countries.filter(n=>countries.some(c=>c[0]===n))
  :[];

 if(explicit.length)return [...new Set(explicit)];

 const headline=normText([a.title,a.title_ko].filter(Boolean).join(' '));
 const summary=normText(a.summary);

 const match=t=>countries
  .filter(c=>c[3].some(k=>aliasMatch(t,k)))
  .map(c=>c[0]);

 const fromTitle=match(headline);
 return fromTitle.length?fromTitle:match(summary);
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
   (category==='바이오'&&(
    cat===norm('바이오')||
    BIO_CATEGORIES.some(c=>norm(c)===cat)
   ));

  const regionOK=region==='전체'||a.region===region;
  const subOK=sub==='전체'||a.subcategory===sub;

  const queryOK=!query||[
   a.title,a.title_ko,a.summary,a.source,
   a.category,a.subcategory,...a.countries
  ].join(' ').toLocaleLowerCase().includes(query);

  return catOK&&regionOK&&subOK&&queryOK;
 });
}

function item(a,cls){
 const url=String(a.url||'');
 const href=/^https?:\/\//i.test(url)?safe(url):'#';

 return `<a class="${cls}" href="${href}" target="_blank" rel="noopener noreferrer">
 <span class="category">${safe(a.category||'일반')}</span>
 <strong>${safe(a.title_ko||a.title||'제목 없음')}</strong>
 ${cls==='latest-item'?`<p>${safe(a.summary||'').slice(0,150)}</p>`:''}
 <span class="meta">${safe(a.region||'')} ${safe(a.subcategory||'')} · ${safe(a.source||'원문')} · ${dateText(a.published)}</span>
 </a>`;
}

function selectCountry(name){
 chosen=name;
 render();
 const c=countries.find(x=>x[0]===name);
 if(c)map.flyTo([c[1],c[2]],Math.max(map.getZoom(),4),{duration:.6});
}

function render(){
 const list=filtered();
 const groups=new Map();

 for(const a of list){
  for(const name of a.countries){
   if(!groups.has(name))groups.set(name,[]);
   groups.get(name).push(a);
  }
 }

 const unclassified=list.filter(a=>!a.countries.length);
 layer.clearLayers();

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

 if($('stat-articles'))$('stat-articles').textContent=all.length;
 if($('stat-countries'))$('stat-countries').textContent=groups.size;

 const selected=chosen?(groups.get(chosen)||[]):list;

 if($('country-title')){
  $('country-title').textContent=chosen?`${chosen} 관련 뉴스`:'전 세계 주요 뉴스';
 }

 if($('country-subtitle')){
  $('country-subtitle').textContent=chosen
   ?`${chosen} 관련 기사 ${selected.length}건 · 전체 목록 표시`
   :`현재 필터 ${list.length}건 · 국가 분류 ${list.length-unclassified.length}건 · 국가 미분류 ${unclassified.length}건 · 지도 마커 ${groups.size}개`;
 }

 if($('country-feed')){
  $('country-feed').innerHTML=selected.length
   ?selected.map(a=>item(a,'country-item')).join('')
   :'<p class="empty">선택한 조건에 해당하는 뉴스가 없습니다.</p>';
 }

 if($('count'))$('count').textContent=`${list.length} ARTICLES`;

 if($('latest-list')){
  $('latest-list').innerHTML=list.length
   ?list.map(a=>item(a,'latest-item')).join('')
   :'<p class="empty">표시할 기사가 없습니다.</p>';
 }

 if($('featured-list')){
  $('featured-list').innerHTML=list.length
   ?list.slice(0,3).map(a=>item(a,'feature-item')).join('')
   :'<p class="empty">표시할 기사가 없습니다.</p>';
 }

 if($('ticker')){
  $('ticker').textContent=list[0]?.title_ko||list[0]?.title||
   '현재 필터에 해당하는 뉴스가 없습니다.';
 }
}

$('category')?.addEventListener('change',()=>{
 chosen=null;
 const m=$('micro-filter');
 if(m){
  m.style.display=$('category').value==='미생물'?'inline-block':'none';
  m.value='전체';
 }
 render();
});

$('search')?.addEventListener('input',()=>{chosen=null;render();});
$('region-filter')?.addEventListener('change',()=>{chosen=null;render();});
$('micro-filter')?.addEventListener('change',()=>{chosen=null;render();});

$('reset')?.addEventListener('click',()=>{
 chosen=null;
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
 $('today').textContent=new Date().toLocaleDateString('ko-KR',{
  year:'numeric',month:'long',day:'numeric'
 });
}

window.addEventListener('resize',()=>map.invalidateSize());

(async()=>{
 try{
  const r=await fetch(DATA_URL+'?t='+Date.now(),{cache:'no-store'});
  if(!r.ok)throw Error(`HTTP ${r.status}`);

  const data=await r.json();

  all=(Array.isArray(data.articles)?data.articles:[])
   .filter(a=>a&&a.title&&/^https?:\/\//i.test(a.url||''))
   .map(a=>({...a,countries:matchedCountries(a)}))
   .sort((a,b)=>new Date(b.published)-new Date(a.published));

  if($('updated')){
   $('updated').textContent=data.updated
    ?`업데이트 ${dateText(data.updated)}`
    :'업데이트 정보 없음';
  }

  render();
  setTimeout(()=>map.invalidateSize(),200);

 }catch(e){
  if($('ticker'))$('ticker').textContent='뉴스 데이터를 불러오지 못했습니다.';

  if($('country-feed')){
   $('country-feed').innerHTML=
    '<p class="empty">data/articles.json 파일과 뉴스 수집 작업을 확인하세요.</p>';
  }

  if($('latest-list')){
   $('latest-list').innerHTML=
    '<p class="empty">뉴스 데이터 로딩 실패: '+safe(e.message)+'</p>';
  }

  if($('featured-list')){
   $('featured-list').innerHTML=
    '<p class="empty">데이터를 불러올 수 없습니다.</p>';
  }

  console.error(e);
 }
})();
