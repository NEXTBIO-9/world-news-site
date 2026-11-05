/* WORLD NEWS V8 - Map and Bio Filter Fix */

const DATA_URL = './data/articles.json';
const $ = id => document.getElementById(id);

const safe = s => String(s ?? '').replace(
  /[&<>"']/g,
  c => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[c])
);

const dateText = d => {
  const v = new Date(d);
  return isNaN(v.getTime()) ? '' :
    v.toLocaleString('ko-KR', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
};

const countries = [
  ['대한민국',36.5,127.8,['대한민국','한국','남한','south korea','seoul','서울']],
  ['북한',40.3,127.5,['북한','north korea','평양','pyongyang']],
  ['미국',39,-98,['미국','워싱턴','트럼프','바이든','united states','u.s.','usa','washington','white house']],
  ['중국',35,104,['중국','베이징','시진핑','china','beijing','xi jinping']],
  ['일본',36,138,['일본','도쿄','japan','tokyo']],
  ['러시아',61,100,['러시아','모스크바','푸틴','russia','moscow','putin']],
  ['우크라이나',49,32,['우크라이나','키이우','젤렌스키','ukraine','kyiv','zelensky']],
  ['대만',23.7,121,['대만','타이완','taiwan','taipei','타이베이']],
  ['영국',54,-2,['영국','런던','britain','united kingdom','london']],
  ['프랑스',46.5,2.2,['프랑스','파리','france','paris']],
  ['독일',51,10,['독일','베를린','germany','berlin']],
  ['이스라엘',31.5,35,['이스라엘','israel','텔아비브','예루살렘']],
  ['이란',32,53,['이란','테헤란','iran','tehran']],
  ['팔레스타인',31.9,35.2,['팔레스타인','가자','가자지구','palestine','gaza']],
  ['사우디아라비아',24,45,['사우디','saudi arabia','리야드']],
  ['인도',22,79,['인도','뉴델리','india','new delhi']],
  ['파키스탄',30,69,['파키스탄','pakistan']],
  ['튀르키예',39,35,['튀르키예','터키','turkey','türkiye','ankara']],
  ['브라질',-14,-52,['브라질','brazil','브라질리아']],
  ['캐나다',56,-106,['캐나다','canada','오타와']],
  ['멕시코',23,-102,['멕시코','mexico']],
  ['호주',-25,134,['호주','오스트레일리아','australia']],
  ['인도네시아',-2,118,['인도네시아','indonesia']],
  ['베트남',16,108,['베트남','vietnam']],
  ['태국',15,101,['태국','thailand']],
  ['필리핀',12.5,122,['필리핀','philippines']],
  ['이집트',27,30,['이집트','egypt']],
  ['남아프리카공화국',-29,24,['남아공','south africa']],
  ['폴란드',52,19,['폴란드','poland']],
  ['스페인',40,-4,['스페인','spain']],
  ['이탈리아',42.5,12.5,['이탈리아','italy']],
  ['아르헨티나',-34,-64,['아르헨티나','argentina']]
];

const BIO_CATEGORIES = [
  '제약·신약',
  '미생물',
  '의료기기',
  '바이오기업',
  '감염병'
];

const normalize = value => String(value ?? '')
  .normalize('NFKC')
  .trim()
  .replace(/\s+/g, '')
  .replace(/[·ㆍ・]/g, '·')
  .toLocaleLowerCase();

const map = L.map('map', {
  worldCopyJump: true,
  minZoom: 2,
  maxZoom: 7,
  zoomControl: true
}).setView([22,15],2);

L.tileLayer(
  'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  }
).addTo(map);

const layer = L.layerGroup().addTo(map);

let all = [];
let chosen = null;

function matchedCountries(article) {
  const title = String(article.title || '').toLocaleLowerCase();

  return countries
    .filter(c =>
      c[3].some(keyword =>
        title.includes(keyword.toLocaleLowerCase())
      )
    )
    .map(c => c[0]);
}

function categoryMatches(articleCategory, selectedCategory) {
  const article = normalize(articleCategory || '일반');
  const selected = normalize(selectedCategory);

  if (selected === normalize('전체')) return true;

  if (selected === normalize('바이오')) {
    return article === normalize('바이오') ||
      BIO_CATEGORIES.some(c => normalize(c) === article);
  }

  return article === selected;
}

function filtered() {
  const category = $('category').value;
  const query = $('search').value.trim().toLocaleLowerCase();

  return all.filter(a => {
    const categoryOK = categoryMatches(a.category, category);

    const searchText = [
      a.title,
      a.source,
      a.category,
      ...(a.countries || [])
    ].join(' ').toLocaleLowerCase();

    return categoryOK && (!query || searchText.includes(query));
  });
}

function item(a, cls) {
  const title = safe(a.title || '제목 없음');
  const category = safe(a.category || '일반');
  const source = safe(a.source || '원문');
  const url = safe(a.url);
  const summary = safe(a.summary || '').slice(0,150);

  return `
    <a class="${cls}" href="${url}"
       target="_blank" rel="noopener noreferrer">
      <span class="category">${category}</span>
      <strong>${title}</strong>
      ${cls === 'latest-item' ? `<p>${summary}</p>` : ''}
      <span class="meta">
        ${source} · ${dateText(a.published)}
      </span>
    </a>
  `;
}

function selectCountry(name) {
  chosen = name;
  render();

  const country = countries.find(c => c[0] === name);

  if (country) {
    map.flyTo(
      [country[1], country[2]],
      Math.max(map.getZoom(),4),
      {duration:0.6}
    );
  }
}

function render() {
  const list = filtered();
  const groups = new Map();

  for (const article of list) {
    for (const name of article.countries) {
      if (!groups.has(name)) groups.set(name, []);
      groups.get(name).push(article);
    }
  }

  layer.clearLayers();

  for (const country of countries) {
    const articles = groups.get(country[0]);

    if (!articles || !articles.length) continue;

    const icon = L.divIcon({
      className: '',
      html: `
        <div class="news-pin ${
          chosen === country[0] ? 'selected' : ''
        }">${articles.length}</div>
      `,
      iconSize: [25,25],
      iconAnchor: [12,12]
    });

    const marker = L.marker(
      [country[1],country[2]],
      {
        icon,
        title: `${country[0]} 관련 기사 ${articles.length}건`
      }
    ).addTo(layer);

    marker.on('click', () => selectCountry(country[0]));
    marker.bindTooltip(`${country[0]} · ${articles.length}건`);
  }

  $('stat-articles').textContent = all.length;
  $('stat-countries').textContent = groups.size;

  const selected = chosen ? (groups.get(chosen) || []) : list;

  $('country-title').textContent = chosen
    ? `${chosen} 관련 뉴스`
    : '전 세계 주요 뉴스';

  $('country-subtitle').textContent = chosen
    ? `제목에서 ${chosen} 관련 표현이 확인된 기사 ${selected.length}건`
    : `현재 선택한 분야의 뉴스 ${selected.length}건`;

  $('country-feed').innerHTML = selected.length
    ? selected.slice(0,35).map(a => item(a,'country-item')).join('')
    : '<p class="empty">선택한 조건에 해당하는 뉴스가 없습니다.</p>';

  $('count').textContent = `${list.length} ARTICLES`;

  $('latest-list').innerHTML = list.length
    ? list.slice(0,60).map(a => item(a,'latest-item')).join('')
    : '<p class="empty">표시할 기사가 없습니다.</p>';

  $('featured-list').innerHTML = list.length
    ? list.slice(0,3).map(a => item(a,'feature-item')).join('')
    : '<p class="empty">표시할 기사가 없습니다.</p>';

  $('ticker').textContent = list[0]?.title ||
    '선택한 조건에 해당하는 뉴스가 없습니다.';

  setTimeout(() => map.invalidateSize(),100);
}

/* 분야 변경 시 이전 국가 선택 자동 해제 */
$('category').addEventListener('change', () => {
  chosen = null;
  render();
});

/* 검색 변경 시에도 국가 선택 해제 */
$('search').addEventListener('input', () => {
  chosen = null;
  render();
});

/* 전체 지도 보기 */
$('reset').addEventListener('click', () => {
  chosen = null;
  $('category').value = '전체';
  $('search').value = '';
  map.setView([22,15],2);
  render();
});

$('today').textContent =
  new Date().toLocaleDateString('ko-KR', {
    year:'numeric',
    month:'long',
    day:'numeric'
  });

/* 뉴스 데이터 불러오기 */
(async () => {
  try {
    const response = await fetch(
      DATA_URL + '?t=' + Date.now(),
      {cache:'no-store'}
    );

    if (!response.ok) {
      throw Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    all = (
      Array.isArray(data.articles) ? data.articles : []
    )
      .filter(a =>
        a &&
        a.title &&
        /^https?:\/\//.test(a.url || '')
      )
      .map(a => ({
        ...a,
        category: String(a.category || '일반').trim(),
        countries: matchedCountries(a)
      }))
      .sort(
        (a,b) =>
          new Date(b.published) - new Date(a.published)
      );

    $('updated').textContent = data.updated
      ? `업데이트 ${dateText(data.updated)}`
      : '업데이트 정보 없음';

    render();

    setTimeout(() => map.invalidateSize(),300);

  } catch (error) {
    $('ticker').textContent =
      '뉴스 데이터를 불러오지 못했습니다.';

    $('country-feed').innerHTML =
      '<p class="empty">뉴스 데이터 로딩 실패</p>';

    $('latest-list').innerHTML =
      `<p class="empty">오류: ${safe(error.message)}</p>`;

    $('featured-list').innerHTML =
      '<p class="empty">데이터를 불러올 수 없습니다.</p>';
  }
})();
