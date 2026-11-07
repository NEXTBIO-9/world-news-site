/* NEXT BIO source-grounded right-side summaries; independent of news/map/bookmarks. */
(() => {
  'use strict';
  const feed = document.getElementById('latest-list');
  if (!feed) return;
  const byUrl = new Map();
  const normalize = s => String(s || '').replace(/\s+/g, ' ').trim();
  function fallback(a) {
    if (!a) return '';
    const title = normalize(a.title).toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');
    const summary = normalize(a.summary_ko || a.summary);
    const text = summary.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '');
    if (text.length < 90 || text.startsWith(title) || title.startsWith(text)) return '';
    return summary.slice(0, 390);
  }
  let busy = false;
  function render() {
    if (busy) return;
    busy = true;
    try {
      feed.querySelectorAll('.nb-news-row').forEach(row => {
        const link = row.querySelector(':scope > a.latest-item');
        if (!link) return;
        let panel = row.querySelector(':scope > .nb-right-summary');
        if (!panel) {
          panel = document.createElement('aside');
          panel.className = 'nb-right-summary';
          panel.setAttribute('aria-label', '기사 요약');
          row.insertBefore(panel, row.querySelector(':scope > .nb2-bookmark') || null);
        }
        const a = byUrl.get(link.getAttribute('href'));
        const content = a && (a.excerpt || fallback(a.article));
        const signature = content || '__empty__';
        if (panel.dataset.signature === signature) return;
        panel.dataset.signature = signature;
        panel.replaceChildren();
        const heading = document.createElement('span');
        heading.className = 'nb-right-summary-label';
        heading.textContent = a && a.excerpt ? '기사 요약 · 원문 발췌' : content ? '기사 요약 · RSS 설명' : '기사 요약';
        const body = document.createElement('p');
        body.textContent = content || '기사 본문을 확보하지 못해 요약을 제공할 수 없습니다.';
        panel.classList.toggle('nb-summary-empty', !content);
        panel.append(heading, body);
      });
    } finally { busy = false; }
  }
  Promise.allSettled([
    fetch('./data/articles.json', {cache:'no-store'}).then(r => {if (!r.ok) throw Error('articles'); return r.json();}),
    fetch('./data/article-summaries.json', {cache:'no-store'}).then(r => {if (!r.ok) return {}; return r.json();})
  ]).then(([news, summaries]) => {
    const articles = news.status === 'fulfilled' ? news.value.articles || [] : [];
    const cache = summaries.status === 'fulfilled' ? summaries.value.summaries || {} : {};
    articles.forEach(article => {
      if (article.url) byUrl.set(article.url, {article, excerpt: normalize(cache[article.url] && cache[article.url].text)});
    });
    render();
  }).catch(() => render());
  const observer = new MutationObserver(render);
  observer.observe(feed, {childList:true, subtree:true});
  render();
})();
