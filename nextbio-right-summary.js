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
  const koreanEnabled = () => window.NBTitleTranslation ? window.NBTitleTranslation.enabled() : (() => { try { return localStorage.getItem('nextbio-title-translation') !== 'off'; } catch (_) { return true; } })();
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
        const ko = koreanEnabled();
        const cached = a && a.cached;
        const excerpt = cached && normalize(ko ? (cached.text_ko || cached.text) : (cached.text || cached.text_ko));
        const content = a && (excerpt || fallback(a.article));
        // When article text is unavailable, show only information actually stated in the headline.
        // This is explicitly NOT an article summary and never invents missing facts.
        const headline = normalize(a && ((ko ? (a.article.title_ko || a.article.title) : (a.article.title || a.article.title_ko))) || link.querySelector('.latest-title')?.textContent || link.textContent);
        const headlineFallback = !content && headline ? headline.slice(0, 260) : '';
        const displayed = content || headlineFallback;
        const signature = (ko ? 'ko:' : 'original:') + (content ? 'summary:' : 'headline:') + displayed;
        if (panel.dataset.signature === signature) return;
        panel.dataset.signature = signature;
        panel.replaceChildren();
        const heading = document.createElement('span');
        heading.className = 'nb-right-summary-label';
        heading.textContent = excerpt ? (ko && cached.text_ko ? '기사 요약 · 한국어 번역' : '기사 요약 · 원문 발췌') : content ? '기사 요약 · RSS 설명' : headlineFallback ? '제목 기준 · 본문 미확보' : '기사 요약';
        const body = document.createElement('p');
        body.textContent = displayed || '기사 본문과 제목 정보를 확보하지 못했습니다.';
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
      if (article.url) byUrl.set(article.url, {article, cached: cache[article.url] || null});
    });
    render();
  }).catch(() => render());
  document.addEventListener('nb-title-translation-changed', render);
  const observer = new MutationObserver(render);
  observer.observe(feed, {childList:true, subtree:true});
  render();
})();
