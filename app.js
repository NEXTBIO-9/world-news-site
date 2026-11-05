const DATA_URL = "./data/articles.json";
let allArticles = [];
const $ = (id) => document.getElementById(id);
const esc = (s="") => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function dateLabel(value){const d=new Date(value);return isNaN(d)? "": d.toLocaleString("ko-KR",{month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"});}
function card(a, featured=false){
  const href = a.url || "#";
  return `<a class="${featured?"feature-card":"article"}" href="${esc(href)}" target="_blank" rel="noopener noreferrer">
    ${featured?`<span class="tag">${esc(a.category||"뉴스")}</span>`:`<span class="category">${esc(a.category||"뉴스")}</span>`}
    <div><h3>${esc(a.title||"제목 없음")}</h3>${featured?`<p>${esc(a.summary||"원문을 확인하세요.")}</p>`:`<p>${esc(a.summary||"원문을 확인하세요.")}</p>`}</div>
    ${featured?`<span class="meta">${esc(a.source||"출처")} · ${dateLabel(a.published)}</span>`:`<time>${dateLabel(a.published)}<br>${esc(a.source||"")}</time>`}
  </a>`;
}
function render(category="전체"){
  const list = category==="전체" ? allArticles : allArticles.filter(a=>a.category===category);
  $("count").textContent = `${list.length} ARTICLES`;
  $("articles").innerHTML = list.length ? list.map(a=>card(a)).join("") : `<div class="loading">해당 분류의 기사가 없습니다.</div>`;
}
async function init(){
  try{
    const res=await fetch(DATA_URL+"?v="+Date.now());
    if(!res.ok) throw new Error("뉴스 데이터가 아직 생성되지 않았습니다.");
    const data=await res.json();
    allArticles=(data.articles||[]).sort((a,b)=>new Date(b.published)-new Date(a.published));
    $("updated").textContent = data.updated ? `최근 업데이트 ${dateLabel(data.updated)}` : "최신 데이터";
    $("featured").innerHTML=allArticles.slice(0,3).map(a=>card(a,true)).join("") || `<div class="loading">표시할 뉴스가 없습니다.</div>`;
    render();
  }catch(e){
    $("featured").innerHTML=`<div class="loading">뉴스 데이터가 아직 준비되지 않았습니다. GitHub Actions에서 뉴스 수집 작업을 한 번 실행해 주세요.</div>`;
    $("articles").innerHTML=`<div class="loading">${esc(e.message)}<br>설치 안내의 첫 실행 단계를 확인하세요.</div>`;
  }
}
$("filters").addEventListener("click",e=>{
  const b=e.target.closest("button[data-category]"); if(!b)return;
  document.querySelectorAll(".filters button").forEach(x=>x.classList.remove("selected"));
  b.classList.add("selected"); render(b.dataset.category);
});
init();
