/**
 * "Related" block for long-form pages on the janaka.me sub-sites.
 *
 * On partials:loaded, if the page has an element with data-related, fetch
 * /assets/content-index.json (built by scripts/gen-content-index.py) and
 * fill it with up to three other pages from the same section, newest first.
 * Uses the shared .card / .chips classes from theme.css; no page-local CSS.
 *
 *   <div data-related class="sec"></div>   just before </main>
 *   <script src="/assets/js/related.js"></script>   after site-nav.js
 */
(function () {
  'use strict';

  var INDEX_URL = '/assets/content-index.json';
  var MAX = 3;
  var LABEL = { blog: 'Blog', academy: 'Academy', lab: 'Lab', ai: 'AI', products: 'Products' };

  function norm(path) {
    try { path = decodeURIComponent(path); } catch (e) {}
    return path.replace(/\/index\.html$/, '/');
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function card(e) {
    var art = el('article', 'card related-card');
    art.appendChild(el('p', 'sub', (LABEL[e.section] || e.section) + ' · ' + (e.minutes || 1) + ' min'));
    var h = el('h3');
    var a = el('a', null, e.title);
    a.href = e.url;
    h.appendChild(a);
    art.appendChild(h);
    if (e.description) art.appendChild(el('p', 'related-desc', e.description));
    var tags = (e.tags || []).filter(function (t) { return t !== e.section; }).slice(0, 3);
    if (tags.length) {
      var chips = el('div', 'chips');
      tags.forEach(function (t) { chips.appendChild(el('span', 'chip', t)); });
      art.appendChild(chips);
    }
    return art;
  }

  function render(host, items) {
    var wrap = el('div', 'wrap');
    wrap.appendChild(el('p', 'eyebrow', 'Related'));
    var grid = el('div', 'cards3 related-grid');
    items.forEach(function (e) { grid.appendChild(card(e)); });
    wrap.appendChild(grid);
    host.innerHTML = '';
    host.appendChild(wrap);
    host.setAttribute('aria-label', 'Related pages');
  }

  function boot() {
    var host = document.querySelector('[data-related]');
    if (!host || host.dataset.relatedDone) return;
    host.dataset.relatedDone = '1';
    var here = norm(location.pathname);
    var section = (location.pathname.split('/')[1] || '').toLowerCase();

    fetch(INDEX_URL, { cache: 'force-cache' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (index) {
        var self = null;
        index.forEach(function (e) { if (norm(e.url) === here) self = e; });
        var sec = self ? self.section : section;
        var items = index
          .filter(function (e) { return e.section === sec && norm(e.url) !== here; })
          .sort(function (a, b) { return a.date < b.date ? 1 : a.date > b.date ? -1 : 0; })
          .slice(0, MAX);
        if (items.length) render(host, items);
        else host.hidden = true;
      })
      .catch(function () { host.hidden = true; });
  }

  window.addEventListener('partials:loaded', boot);
})();
