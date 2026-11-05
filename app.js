
/* WORLD NEWS V11 - Map & Article Display Fix */

const DATA_URL = './data/articles.json';
const $ = id => document.getElementById(id);

const safe = s => String(s ?? '').replace(/[&<>"']/g, c => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
}[c]));

const dateText = d => {
  const v = new Date(d);
  return isNaN(v) ? '' : v.toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const countries = [
  ['대한민국',36.5,127.8,['대한민국','한국','남한','south korea','seoul','서울','korean']],
  ['북한',40.3,127.5,['북한','north korea','평양','pyongyang']],
  ['미국',39,-98,['미국','워싱턴','트럼프','바이든','united states','u.s.','usa','washington','white house','american']],
  ['중국',35,104,['중국','베이징','시진핑','china','beijing','chinese']],
  ['일본',36,138,['일본','도쿄','japan','tokyo','japanese']],
  ['러시아',61,100,['러시아','모스크바','푸틴','russia','moscow','putin','russian']],
  ['우크라이나',49,32,['우크라이나','키이우','젤렌스키','ukraine','kyiv','zelensky']],
  ['대만',23.7,121,['대만','타이완','taiwan','taipei','타이베이']],
  ['영국',54,-2,['영국','런던','britain','united kingdom','london','british','uk']],
  ['프랑스',46.5,2.2,['프랑스','파리','france','paris','french']],
  ['독일',51,10,['독일','베를린','germany','berlin','german']],
  ['이스라엘',31.5,35,['이스라엘','israel','텔아비브','예루살렘']],
  ['이란',32,53,['이란','테헤란','iran','tehran']],
  ['팔레스타인',31.9,35.2,['팔레스타인','가자','가자지구','palestine','gaza']],
  ['사우디아라비아',24,45,['사우디','saudi arabia','리야드']],
  ['인도',22,79,['인도','뉴델리','india','new delhi','indian']],
  ['파키스탄',30,69,['파키스탄','pakistan']],
  ['튀르키예',39,35,['튀르키예','터키','turkey','türkiye','ankara']],
  ['브라질',-14,-52,['브라질','brazil','브라질리아']],
  ['캐나다',56,-106,['캐나다','canada','오타와','canadian']],
  ['멕시코',23,-102,['멕시코','mexico']],
  ['호주',-25,134,['호주','오스트레일리아','australia','australian']],
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

const normalize = s => String(s ?? '')
  .normalize('NFKC')
  .trim()
  .replace(/\s+/g, '')
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

/* 국가명 검색 - 제목과 요약 검사 */
function matchedCountries(article) {
  if (Array.isArray(article.countries) && article.countries.length) {
    return article.countries.filter(name =>
      countries.some(c => c[0] === name)
    );
  }

  const content = [
    article.title,
    article.title_ko,
    article.summary
  ].filter(Boolean).join(' ').toLocaleLowerCase();

  return countries
    .filter(c => c[3].some(keyword => {
      const k = keyword.toLocaleLowerCase();

      // 짧은 영어 약어는 단어 경계 확인
      if (/^[a-z.]{1,3}$/.test(k)) {
        const escaped = k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        return new RegExp(`(^|[^a-z])${escaped}(?=$|[^a-z])`).test(content);
      }

      return content.includes(k);
    }))
    .map(c => c[0]);
}

/* 필터 */
function filtered() {
  const category = $('category')?.value || '전체';
  const query = ($('search')?.value || '').trim().toLocaleLowerCase();
  const region = $('region-filter')?.value || '전체';
  const sub = $('micro-filter')?.value || '전체';

  return all.filter(a => {
    const cat = normalize(a.category);
    const selected = normalize(category);

    const catOK =
      category === '전체' ||
      cat === selected ||
      (
        category === '바이오' &&
        (
          cat === normalize('바이오') ||
          BIO_CATEGORIES.some(c => normalize(c) === cat)
        )
      );

    const regionOK =
      region === '전체' ||
      a.region === region;

    const subOK =
      sub === '전체' ||
      a.subcategory === sub;

    const queryOK =
      !query ||
      [
        a.title,
        a.title_ko,
        a.summary,
        a.source,
        a.category,
        a.subcategory,
        ...(a.countries || [])
      ].join(' ').toLocaleLowerCase().includes(query);

    return catOK && regionOK && subOK && queryOK;
  });
}

/* 기사 카드 */
function item(a, cls) {
  const url = String(a.url || '');
  const href = /^https?:\/\//i.test(url) ? safe(url) : '#';

  return `
    <a class="${cls}"
       href="${href}"
       target="_blank"
       rel="noopener noreferrer">

      <span class="category">
        ${safe(a.category || '일반')}
      </span>

      <strong>
        ${safe(a.title_ko || a.title || '제목 없음')}
      </strong>

      ${cls === 'latest-item'
        ? `<p>${safe(a.summary || '').slice(0,150)}</p>`
        : ''
      }

      <span class="meta">
        ${safe(a.region || '')}
        ${safe(a.subcategory || '')}
        · ${safe(a.source || '원문')}
        · ${dateText(a.published)}
      </span>
    </a>
  `;
}

/* 국가 선택 */
function selectCountry(name) {
  chosen = name;
  render();

  const country = countries.find(c => c[0] === name);

  if (country) {
    map.flyTo(
      [country[1], country[2]],
      Math.max(map.getZoom(), 4),
      {duration: 0.6}
    );
  }
}

/* 전체 화면 갱신 */
function render() {
  const list = filtered();
  const groups = new Map();

  for (const a of list) {
    for (const name of a.countries || []) {
      if (!groups.has(name)) groups.set(name, []);
      groups.get(name).push(a);
    }
  }

  const unclassified = list.filter(
    a => !a.countries || a.countries.length === 0
  );

  layer.clearLayers();

  for (const c of countries) {
    const articles = groups.get(c[0]);

    if (!articles || articles.length === 0) continue;

    const icon = L.divIcon({
      className: '',
      html: `
        <div class="news-pin ${chosen === c[0] ? 'selected' : ''}">
          ${articles.length}
        </div>
      `,
      iconSize: [30,30],
      iconAnchor: [15,15]
    });

    const marker = L.marker(
      [c[1], c[2]],
      {
        icon,
        title: `${c[0]} 관련 기사 ${articles.length}건`
      }
    ).addTo(layer);

    marker.on('click', () => selectCountry(c[0]));
    marker.bindTooltip(`${c[0]} · ${articles.length}건`);
  }

  if ($('stat-articles')) {
    $('stat-articles').textContent = all.length;
  }

  if ($('stat-countries')) {
    $('stat-countries').textContent = groups.size;
  }

  const selected = chosen
    ? (groups.get(chosen) || [])
    : list;

  if ($('country-title')) {
    $('country-title').textContent = chosen
      ? `${chosen} 관련 뉴스`
      : '전 세계 주요 뉴스';
  }

  if ($('country-subtitle')) {
    $('country-subtitle').textContent = chosen
      ? `${chosen} 관련 기사 ${selected.length}건 · 전체 목록 표시`
      : `현재 필터 ${list.length}건 · 국가 분류 ${list.length - unclassified.length}건 · 국가 미분류 ${unclassified.length}건 · 지도 마커 ${groups.size}개`;
  }

  /* 35건 제한 제거 */
  if ($('country-feed')) {
    $('country-feed').innerHTML = selected.length
      ? selected.map(a => item(a,'country-item')).join('')
      : '<p class="empty">선택한 조건에 해당하는 뉴스가 없습니다.</p>';
  }

  if ($('count')) {
    $('count').textContent = `${list.length} ARTICLES`;
  }

  /* 200건 제한 제거 */
  if ($('latest-list')) {
    $('latest-list').innerHTML = list.length
      ? list.map(a => item(a,'latest-item')).join('')
      : '<p class="empty">표시할 기사가 없습니다.</p>';
  }

  if ($('featured-list')) {
    $('featured-list').innerHTML = list.length
      ? list.slice(0,3).map(a => item(a,'feature-item')).join('')
      : '<p class="empty">표시할 기사가 없습니다.</p>';
  }

  if ($('ticker')) {
    $('ticker').textContent =
      list[0]?.title_ko ||
      list[0]?.title ||
      '현재 필터에 해당하는 뉴스가 없습니다.';
  }
}

/* 필터 이벤트 */
$('category')?.addEventListener('change', () => {
  chosen = null;

  const m = $('micro-filter');

  if (m) {
    m.style.display =
      $('category').value === '미생물'
        ? 'inline-block'
        : 'none';

    m.value = '전체';
  }

  render();
});

$('search')?.addEventListener('input', () => {
  chosen = null;
  render();
});

$('region-filter')?.addEventListener('change', () => {
  chosen = null;
  render();
});

$('micro-filter')?.addEventListener('change', () => {
  chosen = null;
  render();
});

$('reset')?.addEventListener('click', () => {
  chosen = null;

  if ($('category')) $('category').value = '전체';
  if ($('search')) $('search').value = '';
  if ($('region-filter')) $('region-filter').value = '전체';

  if ($('micro-filter')) {
    $('micro-filter').value = '전체';
    $('micro-filter').style.display = 'none';
  }

  map.setView([22,15],2);
  render();
});

/* 날짜 */
if ($('today')) {
  $('today').textContent = new Date().toLocaleDateString(
    'ko-KR',
    {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    }
  );
}

window.addEventListener('resize', () => {
  map.invalidateSize();
});

/* 뉴스 데이터 로딩 */
(async () => {
  try {
    const response = await fetch(
      DATA_URL + '?t=' + Date.now(),
      {cache: 'no-store'}
    );

    if (!response.ok) {
      throw Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    all = (
      Array.isArray(data.articles)
        ? data.articles
        : []
    )
      .filter(a =>
        a &&
        a.title &&
        /^https?:\/\//i.test(a.url || '')
      )
      .map(a => ({
        ...a,
        countries: matchedCountries(a)
      }))
      .sort(
        (a,b) =>
          new Date(b.published) -
          new Date(a.published)
      );

    if ($('updated')) {
      $('updated').textContent = data.updated
        ? `업데이트 ${dateText(data.updated)}`
        : '업데이트 정보 없음';
    }

    render();

    setTimeout(() => map.invalidateSize(), 200);

  } catch (error) {
    if ($('ticker')) {
      $('ticker').textContent =
        '뉴스 데이터를 불러오지 못했습니다.';
    }

    if ($('country-feed')) {
      $('country-feed').innerHTML =
        '<p class="empty">data/articles.json 파일과 뉴스 수집 작업을 확인하세요.</p>';
    }

    if ($('latest-list')) {
      $('latest-list').innerHTML =
        '<p class="empty">뉴스 데이터 로딩 실패: ' +
        safe(error.message) +
        '</p>';
    }

    if ($('featured-list')) {
      $('featured-list').innerHTML =
        '<p class="empty">데이터를 불러올 수 없습니다.</p>';
    }

    console.error('WORLD NEWS V11:', error);
  }
})();
