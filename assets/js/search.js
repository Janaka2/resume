/**
 * Site search overlay for the janaka.me sub-sites.
 *
 * Opens on "/" (when focus is not in a text field) or on a click of any
 * element carrying data-search-open. Fetches /assets/content-index.json once
 * (built by scripts/gen-content-index.py), filters on title + description +
 * tags, ranks title matches first and lists up to 12 results.
 *
 * site-nav.js injects this file on first use, so most page views never load
 * it. It also works when linked directly. Styles: .search-* in subsite.css.
 */
(function () {
  'use strict';
  if (window.jpSearch) return;

  var INDEX_URL = '/assets/content-index.json';
  var MAX = 12;
  var LABEL = { blog: 'Blog', academy: 'Academy', lab: 'Lab', ai: 'AI', products: 'Products' };

  var overlay, panel, input, list, hint, closeBtn;
  var index = null, loading = null, lastFocus = null, isOpen = false;

  /* ---------- data ---------- */
  function load() {
    if (index) return Promise.resolve(index);
    if (!loading) {
      loading = fetch(INDEX_URL, { cache: 'force-cache' })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(function (data) {
          index = data.map(function (e) {
            return {
              e: e,
              title: (e.title || '').toLowerCase(),
              desc: (e.description || '').toLowerCase(),
              tags: (e.tags || []).join(' ').toLowerCase()
            };
          });
          return index;
        })
        .catch(function (err) { loading = null; throw err; });
    }
    return loading;
  }

  function search(q) {
    q = (q || '').trim().toLowerCase();
    if (!q) return index.slice(0, MAX).map(function (r) { return r.e; });
    var tokens = q.split(/\s+/);
    var hits = [];
    for (var i = 0; i < index.length; i++) {
      var r = index[i], score = 0, ok = true;
      for (var t = 0; t < tokens.length; t++) {
        var tok = tokens[t];
        var inTitle = r.title.indexOf(tok) !== -1;
        var inTags = r.tags.indexOf(tok) !== -1;
        var inDesc = r.desc.indexOf(tok) !== -1;
        if (!inTitle && !inTags && !inDesc) { ok = false; break; }
        score += inTitle ? 10 : 0;
        score += inTags ? 3 : 0;
        score += inDesc ? 1 : 0;
      }
      if (!ok) continue;
      if (r.title.indexOf(q) !== -1) score += 100;
      hits.push({ score: score, e: r.e });
    }
    hits.sort(function (a, b) {
      return b.score - a.score || (b.e.date > a.e.date ? 1 : b.e.date < a.e.date ? -1 : 0);
    });
    return hits.slice(0, MAX).map(function (h) { return h.e; });
  }

  /* ---------- markup ---------- */
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function build() {
    if (overlay) return;
    overlay = el('div', 'search-overlay');
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Search the site');
    overlay.hidden = true;

    panel = el('div', 'search-panel');
    var head = el('div', 'search-head');
    input = el('input', 'search-input');
    input.type = 'search';
    input.placeholder = 'Search articles, modules and notes';
    input.setAttribute('aria-label', 'Search');
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('spellcheck', 'false');
    closeBtn = el('button', 'iconbtn search-close', '✕');
    closeBtn.type = 'button';
    closeBtn.setAttribute('aria-label', 'Close search');
    head.appendChild(input);
    head.appendChild(closeBtn);

    hint = el('p', 'search-hint', 'Type to search. Esc closes.');
    hint.setAttribute('aria-live', 'polite');
    list = el('ul', 'search-results');

    panel.appendChild(head);
    panel.appendChild(hint);
    panel.appendChild(list);
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    input.addEventListener('input', function () { render(input.value); });
    closeBtn.addEventListener('click', close);
    overlay.addEventListener('click', function (ev) { if (ev.target === overlay) close(); });
    overlay.addEventListener('keydown', onOverlayKey);
  }

  function render(q) {
    if (!index) return;
    var results = search(q);
    list.innerHTML = '';
    var trimmed = (q || '').trim();
    if (!results.length) {
      hint.textContent = 'Nothing found for “' + trimmed + '”.';
      return;
    }
    hint.textContent = trimmed
      ? results.length + (results.length === 1 ? ' result' : ' results')
      : 'Newest pages. Type to search.';
    results.forEach(function (e) {
      var li = el('li');
      var a = el('a', 'search-hit');
      a.href = e.url;
      a.appendChild(el('span', 'search-section', LABEL[e.section] || e.section));
      a.appendChild(el('span', 'search-title', e.title));
      if (e.description) a.appendChild(el('span', 'search-desc', e.description));
      a.appendChild(el('span', 'search-meta', (e.minutes || 1) + ' min'));
      li.appendChild(a);
      list.appendChild(li);
    });
  }

  /* ---------- open / close / focus trap ---------- */
  function focusables() {
    return Array.prototype.filter.call(
      panel.querySelectorAll('input, button, a[href]'),
      function (n) { return !n.disabled && n.offsetParent !== null; }
    );
  }

  function onOverlayKey(ev) {
    if (ev.key === 'Escape') { ev.preventDefault(); close(); return; }
    var items = focusables();
    if (!items.length) return;
    var i = items.indexOf(document.activeElement);
    if (ev.key === 'Tab') {
      ev.preventDefault();
      var next = ev.shiftKey ? (i <= 0 ? items.length - 1 : i - 1) : (i === -1 || i === items.length - 1 ? 0 : i + 1);
      items[next].focus();
    } else if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
      var links = Array.prototype.slice.call(list.querySelectorAll('a'));
      if (!links.length) return;
      ev.preventDefault();
      var j = links.indexOf(document.activeElement);
      if (ev.key === 'ArrowDown') links[j === -1 || j === links.length - 1 ? 0 : j + 1].focus();
      else if (j <= 0) input.focus();
      else links[j - 1].focus();
    }
  }

  function open() {
    build();
    if (isOpen) { input.focus(); return; }
    isOpen = true;
    lastFocus = document.activeElement;
    overlay.hidden = false;
    document.documentElement.classList.add('search-open');
    input.value = '';
    hint.textContent = 'Loading…';
    list.innerHTML = '';
    input.focus();
    load().then(function () { if (isOpen) render(input.value); })
          .catch(function () { hint.textContent = 'Search is unavailable right now.'; });
  }

  function close() {
    if (!isOpen) return;
    isOpen = false;
    overlay.hidden = true;
    document.documentElement.classList.remove('search-open');
    if (lastFocus && typeof lastFocus.focus === 'function') lastFocus.focus();
    lastFocus = null;
  }

  function inTextField(node) {
    if (!node) return false;
    var tag = (node.tagName || '').toLowerCase();
    return tag === 'input' || tag === 'textarea' || tag === 'select' || node.isContentEditable;
  }

  /* ---------- triggers ---------- */
  document.addEventListener('keydown', function (ev) {
    if (ev.key !== '/' || ev.ctrlKey || ev.metaKey || ev.altKey) return;
    if (isOpen || inTextField(ev.target)) return;
    ev.preventDefault();
    open();
  });
  document.addEventListener('click', function (ev) {
    var t = ev.target && ev.target.closest ? ev.target.closest('[data-search-open]') : null;
    if (!t) return;
    ev.preventDefault();
    open();
  });

  window.jpSearch = { open: open, close: close };
})();
