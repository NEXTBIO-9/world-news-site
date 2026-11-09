/* NEXT BIO ticker translation sync — preserves existing ticker and map. */
(function () {
  'use strict';
  const ROOT = 'nb-emergency-ticker';
  const feeds = ['./data/articles.json', './data/emergency-news.json'];
  let titles = new Map();
  let busy = false;
  const clean = url => { try { return new URL(url, location.href).href.split('#')[0]; } catch (_) { return ''; } };
  function titleOf(article) {
    const translator = window.NBTitleTranslation;
    const translated = translator && typeof translator.title === 'function' ? translator.title(article) :
      ((localStorage.getItem('nextbio-title-translation') === 'off') ? article.title : (article.title_ko || article.title));
    return String(translated || article.title || '').trim().slice(0, 180);
  }
  function apply() {
    const root = document.getElementById(ROOT);
    if (!root) return;
    const links = root.querySelectorAll('.nb-emergency-item[href]');
    links.forEach(link => {
      const article = titles.get(clean(link.href));
      if (!article) return;
      const icon = (link.textContent || '').match(/^(⚔️|🌋|💥|🚨|🚀|🌐)\s*/u)?.[1] || '🌐';
      const wanted = icon + ' ' + titleOf(article);
      if (link.textContent !== wanted) link.textContent = wanted;
    });
  }
  async function load() {
    if (busy) return;
    busy = true;
    try {
      const responses = await Promise.all(feeds.map(async url => {
        try {
          const res = await fetch(url + '?tickerLang=' + Date.now(), {cache:'no-store'});
          return res.ok ? await res.json() : {};
        } catch (_) { return {}; }
      }));
      const all = [...(responses[0].articles || []), ...(responses[1].events || [])];
      const next = new Map();
      all.forEach(article => {
        if (article && article.url) next.set(clean(article.url), article);
      });
      titles = next;
      apply();
    } finally { busy = false; }
  }
  function start() {
    load();
    document.addEventListener('nb-title-translation-changed', apply);
    setInterval(load, 60 * 1000);
    const observer = new MutationObserver(() => {
      const track = document.querySelector('#' + ROOT + ' .nb-emergency-track');
      if (track && observer.track !== track) {
        if (observer.track) observer.disconnect();
        observer.observe(track, {childList:true});
        observer.track = track;
      }
      apply();
    });
    const attach = () => {
      const track = document.querySelector('#' + ROOT + ' .nb-emergency-track');
      if (track) {
        observer.observe(track, {childList:true});
        observer.track = track;
      } else setTimeout(attach, 300);
    };
    attach();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})();
