/* NEXT BIO 2.3 map layout correction: does not alter map data or tour. */
(function () {
  const layout = document.querySelector('.nb-command-center .map-layout');
  const mapColumn = layout && layout.querySelector('.map-col');
  if (!layout || !mapColumn) return;
  let last = 0;
  function syncPanelHeight() {
    if (window.matchMedia('(max-width: 1000px)').matches) {
      layout.style.removeProperty('--nb-map-column-height');
      return;
    }
    const h = Math.ceil(mapColumn.getBoundingClientRect().height);
    if (h > 0 && h !== last) {
      last = h;
      layout.style.setProperty('--nb-map-column-height', h + 'px');
    }
  }
  syncPanelHeight();
  if ('ResizeObserver' in window) {
    new ResizeObserver(syncPanelHeight).observe(mapColumn);
  }
  window.addEventListener('resize', syncPanelHeight, {passive:true});
  window.addEventListener('load', syncPanelHeight, {once:true});
})();
