/* NEXT BIO verified emergency ticker — standalone, no map/feed changes. */
(function () {
  'use strict';
  const STYLE_ID = 'nb-emergency-ticker-style';
  const ROOT_ID = 'nb-emergency-ticker';
  const MAX_AGE_MS = 30 * 60 * 1000;
  const CATEGORIES = [
    {id:'war', icon:'⚔️', label:'전쟁'},
    {id:'disaster', icon:'🌋', label:'대규모 재난'},
    {id:'terror', icon:'💥', label:'테러'},
    {id:'emergency', icon:'🚨', label:'국가비상사태'},
    {id:'battle', icon:'🚀', label:'대규모 전투'}
  ];
  const allowed = new Map(CATEGORIES.map(c => [c.id, c]));
  let refreshTimer = null;
  function stylesheet() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
#${ROOT_ID}{display:flex;align-items:stretch;width:100%;height:48px;margin:12px 0 18px;background:#000;color:#f1f5f9;overflow:hidden;border-radius:4px;font-family:inherit;box-sizing:border-box}
#${ROOT_ID} *{box-sizing:border-box}
#${ROOT_ID} .nb-emergency-label{flex:none;display:flex;align-items:center;justify-content:center;white-space:nowrap;padding:0 16px;background:#b91c1c;color:#fff;font-size:16px;font-weight:900;line-height:1}
#${ROOT_ID}.nb-normal .nb-emergency-label{background:#263b55}
#${ROOT_ID} .nb-emergency-window{position:relative;min-width:0;flex:1;overflow:hidden;display:flex;align-items:center;background:#000}
#${ROOT_ID} .nb-emergency-track{display:flex;align-items:center;flex:none;gap:36px;white-space:nowrap;width:max-content;padding-left:100%;animation:nbEmergencyMove var(--nb-duration,35s) linear infinite}
#${ROOT_ID} .nb-emergency-item{color:#f1f5f9;text-decoration:none;font-size:16px;font-weight:900;line-height:1.4}
#${ROOT_ID} .nb-emergency-item:hover,#${ROOT_ID} .nb-emergency-item:focus-visible{text-decoration:underline;color:#fff}
#${ROOT_ID} .nb-emergency-separator{color:#94a3b8;font-size:15px}
@keyframes nbEmergencyMove{from{transform:translateX(0)}to{transform:translateX(-100%)}}
@media(max-width:620px){#${ROOT_ID} .nb-emergency-label{font-size:14px;padding:0 10px}#${ROOT_ID} .nb-emergency-item{font-size:14px}}
@media(prefers-reduced-motion:reduce){#${ROOT_ID} .nb-emergency-track{animation:none;padding:0 12px;overflow-x:auto;max-width:100%;width:100%}}
`;
    document.head.appendChild(style);
  }
  function install() {
    const mapSection = document.getElementById('map-section');
    if (!mapSection || document.getElementById(ROOT_ID)) return;
    stylesheet();
    const root = document.createElement('section');
    root.id = ROOT_ID;
    root.setAttribute('aria-label', '검증된 긴급속보 및 주요 뉴스');
    const label = document.createElement('div');
    label.className = 'nb-emergency-label';
    const windowEl = document.createElement('div');
    windowEl.className = 'nb-emergency-window';
    const track = document.createElement('div');
    track.className = 'nb-emergency-track';
    windowEl.appendChild(track);
    root.append(label, windowEl);
    const map = document.getElementById('map');
    if (map && map.parentElement) {
      map.insertAdjacentElement('afterend', root);
      root.style.margin = '0 0 10px';
      root.style.borderRadius = '0 0 6px 6px';
    } else {
      mapSection.insertAdjacentElement('afterend', root);
    }
  }
  function verifiedEmergency(article, now) {
    if (article.verified === true && article.type && article.event_time && article.source) {
      const kind = allowed.get(String(article.type));
      const eventAt = Date.parse(article.event_time);
      if (kind && Number.isFinite(eventAt) && eventAt <= now && now - eventAt <= MAX_AGE_MS) return kind;
    }
    // An RSS publication timestamp is NOT proof of the incident time.
    // Upstream verification must explicitly supply these metadata fields.
    if (article.emergency_verified !== true || article.event_time_verified !== true) return null;
    const kind = allowed.get(String(article.emergency_type || ''));
    const eventAt = Date.parse(article.event_time || '');
    const publishedAt = Date.parse(article.published || '');
    if (!kind || !Number.isFinite(eventAt) || !Number.isFinite(publishedAt)) return null;
    if (eventAt > now + 60_000 || now - eventAt > MAX_AGE_MS || now - eventAt < 0) return null;
    if (publishedAt > now + 60_000 || now - publishedAt > MAX_AGE_MS || now - publishedAt < 0) return null;
    return kind;
  }
  function displayTitle(a) {
    const value = a.title_ko || a.title || '';
    return String(value).trim().slice(0, 180);
  }
  function render(articles, verifiedEvents) {
    const root = document.getElementById(ROOT_ID);
    if (!root) return;
    const label = root.querySelector('.nb-emergency-label');
    const track = root.querySelector('.nb-emergency-track');
    const now = Date.now();
    const emergency = [];
    for (const e of verifiedEvents || []) {
      if (!e || e.verified !== true || !/^https:\/\//i.test(String(e.url || ""))) continue;
      const kind = verifiedEmergency(e, now);
      if (!kind) continue;
      const title = displayTitle(e);
      if (title) emergency.push({a:e, title, icon:kind.icon});
    }
    const normal = [];
    const seen = new Set();
    for (const a of articles) {
      if (!a || typeof a !== 'object') continue;
      const title = displayTitle(a);
      const url = String(a.url || '');
      if (!title || !/^https?:\/\//i.test(url)) continue;
      const key = url.split('#')[0];
      if (seen.has(key)) continue;
      seen.add(key);
      const kind = verifiedEmergency(a, now);
      if (kind) emergency.push({a, title, icon:kind.icon});
      else normal.push({a, title, icon:'🌐'});
    }
    const uniqueEmergency = Array.from(new Map(emergency.map(x => [x.a.id || x.a.url, x])).values());
    const active = uniqueEmergency.length > 0;
    root.classList.toggle('nb-normal', !active);
    label.textContent = active ? '긴급속보' : '주요뉴스';
    const selected = (active ? uniqueEmergency : normal.sort((x,y)=>Date.parse(y.a.published||0)-Date.parse(x.a.published||0))).slice(0, 12);
    track.replaceChildren();
    if (!selected.length) {
      const span = document.createElement('span');
      span.className = 'nb-emergency-item';
      span.textContent = '표시할 뉴스가 없습니다.';
      track.appendChild(span);
      track.style.animation = 'none';
      return;
    }
    track.style.animation = '';
    track.style.setProperty('--nb-duration', Math.max(25, selected.length * 7) + 's');
    selected.forEach((item, i) => {
      if (i) {
        const separator = document.createElement('span');
        separator.className = 'nb-emergency-separator';
        separator.textContent = '◆';
        separator.setAttribute('aria-hidden', 'true');
        track.appendChild(separator);
      }
      const a = document.createElement('a');
      a.className = 'nb-emergency-item';
      a.href = item.a.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      a.textContent = item.icon + ' ' + item.title;
      track.appendChild(a);
    });
  }
  async function update() {
    try {
      const response = await fetch('./data/articles.json?nbTicker=' + Math.floor(Date.now()/60000), {cache:'no-store'});
      if (!response.ok) throw new Error('News feed unavailable');
      const data = await response.json();
      if (!Array.isArray(data.articles)) throw new Error('Invalid news feed');
      let verifiedEvents = [];
      try {
        const verifiedResponse = await fetch('./data/emergency-news.json?nbEmergency=' + Math.floor(Date.now()/60000), {cache:'no-store'});
        if (verifiedResponse.ok) {
          const verifiedData = await verifiedResponse.json();
          if (Array.isArray(verifiedData.events)) verifiedEvents = verifiedData.events;
        }
      } catch (_) { /* Keep regular news visible during emergency feed outages. */ }
      render(data.articles, verifiedEvents);
    } catch (err) {
      const root = document.getElementById(ROOT_ID);
      if (root) {
        root.classList.add('nb-normal');
        root.querySelector('.nb-emergency-label').textContent = '주요뉴스';
        const track = root.querySelector('.nb-emergency-track');
        track.replaceChildren();
        track.textContent = '뉴스를 불러오는 중입니다.';
        track.style.animation = 'none';
      }
    }
  }
  function start() {
    install();
    update();
    if (!refreshTimer) refreshTimer = setInterval(update, 60 * 1000);
    document.addEventListener('visibilitychange', () => {if (!document.hidden) update();});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once:true});
  else start();
})();
