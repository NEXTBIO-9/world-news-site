/* WORLD NEWS FINAL — explicit evidence-based country mapping */
'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmtDate=d=>{const x=new Date(d);return Number.isNaN(x.getTime())?'':x.toLocaleString('ko-KR',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});};
const BIO=['제약·신약','미생물','의료기기','바이오기업','감염병'];
let countries=[],countryMap=new Map(),all=[],chosen=null,unclassifiedOnly=false,page=1;
const PAGE_SIZE=60;
const map=L.map('map',{worldCopyJump:true,minZoom:2,maxZoom:7}).setView([22,15],2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OpenStreetMap contributors',maxZoom:19}).addTo(map);
const layer=L.layerGroup().addTo(map);
function articleCountries(a){
  // Never guess from region, language, source or text on the client.
  return [...new Set((Array.isArray(a.countries)?a.countries:[]).filter(n=>countryMap.has(n)))];
}
function filtered(){
 const cat=$('category').value,sub=$('micro-filter').value,region=$('region-filter').value,q=$('search').value.trim().toLocaleLowerCase();
 return all.filter(a=>{
  if(cat!=='전체'&&!(cat==='바이오'?BIO.includes(a.category):cat===a.category))return false;
  if(cat==='미생물'&&sub!=='전체'&&sub!==a.subcategory)return false;
  if(region!=='전체'&&region!==a.region)return false;
  return !q||[a.title,a.title_ko,a.summary,a.source,a.category,a.subcategory,...a.countries].join(' ').toLocaleLowerCase().includes(q);
 });
}
function articleHTML(a,cls){
 const url=String(a.url||''),href=/^https?:\/\//i.test(url)?esc(url):'#';
 const loc=a.countries.length?` · ${esc(a.countries.join(', '))}`:' · 국가 미분류';
 const summary=a.summary&&a.summary.trim()!==a.title.trim()?`<p>${esc(a.summary).slice(0,230)}</p>`:'';
 return `<a class="${cls}" href="${href}" target="_blank" rel="noopener noreferrer"><span class="category">${esc(a.category)}${a.subcategory?' / '+esc(a.subcategory):''}</span><strong>${esc(a.title_ko||a.title)}</strong>${cls==='latest-item'?summary:''}<span class="meta">${esc(a.source||'원문')} · ${fmtDate(a.published)}${loc}</span></a>`;
}
function selectCountry(name){chosen=name;unclassifiedOnly=false;page=1;render();const c=countryMap.get(name);if(c)map.flyTo([c.lat,c.lon],Math.max(map.getZoom(),4),{duration:.6});}
function render(){
 const list=filtered(),groups=new Map(),unclassified=list.filter(a=>!a.countries.length);
 for(const a of list)for(const n of a.countries){if(!groups.has(n))groups.set(n,[]);groups.get(n).push(a);}
 layer.clearLayers();
 for(const c of countries){const articles=groups.get(c.name);if(!articles?.length)continue;
  const icon=L.divIcon({className:'',html:`<div class="news-pin ${chosen===c.name?'selected':''}">${articles.length}</div>`,iconSize:[32,32],iconAnchor:[16,16]});
  const marker=L.marker([c.lat,c.lon],{icon,title:`${c.name} ${articles.length}건`}).addTo(layer);
  marker.on('click',()=>selectCountry(c.name));marker.bindTooltip(`${c.name} · ${articles.length}건`);
 }
 $('stat-articles').textContent=all.length;
 $('stat-countries').textContent=groups.size;
 const selected=unclassifiedOnly?unclassified:(chosen?(groups.get(chosen)||[]):list);
 $('country-title').textContent=unclassifiedOnly?'국가 미분류 뉴스':chosen?`${chosen} 관련 뉴스`:'전 세계 주요 뉴스';
 $('country-subtitle').textContent=unclassifiedOnly?`국가를 확인할 근거가 없는 기사 ${selected.length}건`:chosen?`${chosen} 관련 기사 ${selected.length}건`:`현재 필터 ${list.length}건 · 국가 분류 ${list.length-unclassified.length}건 · 국가 미분류 ${unclassified.length}건 · 지도 마커 ${groups.size}개`;
 $('unclassified-toggle').textContent=unclassifiedOnly?'전체 뉴스 보기':`국가 미분류 보기 (${unclassified.length})`;
 $('country-feed').innerHTML=selected.length?selected.map(a=>articleHTML(a,'country-item')).join(''):'<p class="empty">선택한 조건에 해당하는 뉴스가 없습니다.</p>';
 $('count').textContent=`${list.length} ARTICLES`;
 const maxPage=Math.max(1,Math.ceil(list.length/PAGE_SIZE));page=Math.min(page,maxPage);
 const shown=list.slice((page-1)*PAGE_SIZE,page*PAGE_SIZE);
 $('latest-list').innerHTML=shown.length?shown.map(a=>articleHTML(a,'latest-item')).join(''):'<p class="empty">표시할 기사가 없습니다.</p>';
 $('page-info').textContent=`${page} / ${maxPage} 페이지`;
 $('prev-page').disabled=page<=1;$('next-page').disabled=page>=maxPage;
 $('featured-list').innerHTML=list.length?list.slice(0,3).map(a=>articleHTML(a,'feature-item')).join(''):'<p class="empty">표시할 기사가 없습니다.</p>';
 $('ticker').textContent=list[0]?.title_ko||list[0]?.title||'표시할 뉴스가 없습니다.';
}
function resetSelection(){chosen=null;unclassifiedOnly=false;page=1;render();}
$('category').addEventListener('change',()=>{$('micro-filter').hidden=$('category').value!=='미생물';$('micro-filter').value='전체';resetSelection();});
for(const id of ['search','region-filter','micro-filter'])$(id).addEventListener(id==='search'?'input':'change',resetSelection);
$('unclassified-toggle').addEventListener('click',()=>{unclassifiedOnly=!unclassifiedOnly;chosen=null;page=1;render();});
$('prev-page').addEventListener('click',()=>{page--;render();$('latest').scrollIntoView({behavior:'smooth'});});
$('next-page').addEventListener('click',()=>{page++;render();$('latest').scrollIntoView({behavior:'smooth'});});
$('reset').addEventListener('click',()=>{$('category').value='전체';$('micro-filter').value='전체';$('micro-filter').hidden=true;$('region-filter').value='전체';$('search').value='';chosen=null;unclassifiedOnly=false;page=1;map.setView([22,15],2);render();});
$('today').textContent=new Date().toLocaleDateString('ko-KR',{year:'numeric',month:'long',day:'numeric'});
window.addEventListener('resize',()=>map.invalidateSize());
(async()=>{
 try{
  const [cr,ar]=await Promise.all([fetch('./data/countries.json',{cache:'no-store'}),fetch('./data/articles.json?t='+Date.now(),{cache:'no-store'})]);
  if(!cr.ok||!ar.ok)throw Error(`데이터 응답 오류 ${cr.status}/${ar.status}`);
  countries=await cr.json();countryMap=new Map(countries.map(c=>[c.name,c]));
  const data=await ar.json();
  all=(Array.isArray(data.articles)?data.articles:[]).filter(a=>a&&a.title&&/^https?:\/\//i.test(a.url||'')).map(a=>({...a,countries:articleCountries(a)})).sort((a,b)=>new Date(b.published)-new Date(a.published));
  $('updated').textContent=data.updated?`업데이트 ${fmtDate(data.updated)}`:'업데이트 정보 없음';
  render();setTimeout(()=>map.invalidateSize(),150);
 }catch(e){console.error(e);$('ticker').textContent='뉴스 데이터를 불러오지 못했습니다.';$('country-feed').innerHTML=`<p class="empty">${esc(e.message)}</p>`;$('latest-list').innerHTML='<p class="empty">data 파일과 GitHub Actions를 확인하세요.</p>';}
})();
