/* NEXT BIO: first-visit opening animation only. */
(() => {
  'use strict';
  if (window.__nextbioAtmosphere) return;
  window.__nextbioAtmosphere = true;
  const $ = id => document.getElementById(id);
  const storage = {
    get(k) { try { return localStorage.getItem(k); } catch (_) { return null; } },
    set(k,v) { try { localStorage.setItem(k,v); } catch (_) {} }
  };
  // Show the intro once per browser tab session, not on every refresh.
  let showIntro = true;
  try { showIntro = sessionStorage.getItem('nextbio-intro-seen') !== '1'; sessionStorage.setItem('nextbio-intro-seen','1'); } catch (_) {}
  if (showIntro) {
    const overlay = document.createElement('div');
    overlay.id = 'nb-opening';
    overlay.setAttribute('role','dialog');
    overlay.setAttribute('aria-label','NEXT BIO 시작 화면');
    overlay.innerHTML = '<div class="nb-opening-inner"><div class="nb-opening-logo">NEXT<span>BIO</span></div><div class="nb-opening-sub">GLOBAL BIO &amp; NEWS NETWORK</div><div class="nb-opening-line"></div><button id="nb-opening-skip" type="button">바로 시작</button></div>';
    document.body.appendChild(overlay);
    let closed = false;
    const dismiss = () => { if (closed) return; closed = true; overlay.classList.add('nb-hide'); window.setTimeout(() => overlay.remove(), 650); };
    $('nb-opening-skip').addEventListener('click',dismiss);
    overlay.addEventListener('keydown',e=>{if(e.key==='Escape')dismiss();});
    window.setTimeout(dismiss, window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 300 : 1900);
  }
})();
