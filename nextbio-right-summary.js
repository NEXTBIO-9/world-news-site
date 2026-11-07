/* NEXT BIO right-side news summary; independent of app.js and bookmarks. */
(() => {
  'use strict';
  const feed = document.getElementById('latest-list');
  if (!feed) return;
  const byUrl = new Map();
  const normalize = s => String(s || '').replace(/\s+/g, ' ').trim();
  const trimPublisher = (s, source) => source && s.endsWith(source) ? normalize(s.slice(0, -source.length)) : s;
  function excerpt(article) {
    const title = normalize(article.title);
    const source = normalize(article.source);
    const summary = trimPublisher(normalize(article.summary_ko || article.summary), source);
    if (!summary) return '';
    const clean = summary.replace(/^[·|\-–—: ]+|[·|\-–—: ]+$/g, '').trim();
    const titleNormalized = title.toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');
    const summaryNormalized = clean.toLocaleLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');
    if (!summaryNormalized || summaryNormalized === titleNormalized ||
      summaryNormalized.startsWith(titleNormalized) || titleNormalized.startsWith(summaryNormalized)) return '';
    if (clean.length < 45 || summaryNormalized.length < titleNormalized.length * 0.65) return '';
    return clean.slice(0, 360);
  }
  let busy = false;
  function render() {
    if (busy) return;
    busy = true;
    try {
      feed.querySelectorAll('.nb-news-row').forEach(row => {
        const link = row.querySelector(':scope > a.latest-item');
        if (!link) return;
        const article = byUrl.get(link.getAttribute('href'));
        let panel = row.querySelector(':scope > .nb-right-summary');
        if (!panel) {
          panel = document.createElement('aside');
          panel.className = 'nb-right-summary';
          panel.setAttribute('aria-label', '기사 요약');
          const star = row.querySelector(':scope > .nb2-bookmark');
          row.insertBefore(panel, star || null);
        }
        const content = article && excerpt(article);
        const signature = content || '__empty__';
        if (panel.dataset.signature === signature) return;
        panel.dataset.signature = signature;
        panel.replaceChildren();
        const heading = document.createElement('span');
        heading.className = 'nb-right-summary-label';
        heading.textContent = content ? '기사 요약 · RSS 제공 내용' : '기사 요약';
        const body = document.createElement('p');
        body.textContent = content || '원문에 별도 요약문이 제공되지 않았습니다. 제목을 눌러 기사를 확인하세요.';
        if (!content) panel.classList.add('nb-summary-empty');
        else panel.classList.remove('nb-summary-empty');
        panel.append(heading, body);
      });
    } finally { busy = false; }
  }
  fetch('./data/articles.json', {cache:'no-store'})
    .then(r => { if (!r.ok) throw Error('articles'); return r.json(); })
    .then(data => { (data.articles || []).forEach(a => { if (a.url) byUrl.set(a.url, a); }); render(); })
    .catch(() => render());
  const observer = new MutationObserver(() => render());
  observer.observe(feed, {childList:true, subtree:true});
  render();
})();
