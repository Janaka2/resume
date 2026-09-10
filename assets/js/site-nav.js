/**
 * Sub-site chrome: marks the current section in partials/site-nav.html and
 * wires the theme toggle. The hub at / uses assets/js/main.js instead.
 *
 * Theme is stored under 'jp-theme', the same key the hub and the visual CV
 * use, so a dark-mode choice follows the visitor across every property.
 * The initial value is applied pre-paint by an inline script in each <head>;
 * this file only handles the toggle once the nav has been injected.
 */
(function () {
  'use strict';

  function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  function sectionFromPath() {
    var seg = location.pathname.split('/')[1] || '';
    return seg.toLowerCase().replace(/\.html$/, '') || 'home';
  }

  function markActive() {
    var links = document.querySelectorAll('[data-nav]');
    if (!links.length) return;
    var here = sectionFromPath();
    Array.prototype.forEach.call(links, function (a) {
      var active = a.getAttribute('data-nav') === here;
      a.classList.toggle('active', active);
      if (active) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
  }

  function wireTheme() {
    var btn = document.getElementById('themeBtn');
    if (!btn || btn.dataset.wired) return;
    btn.dataset.wired = '1';
    var root = document.documentElement;
    function reflect() {
      btn.setAttribute('aria-pressed', root.getAttribute('data-theme') === 'dark' ? 'true' : 'false');
    }
    btn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      store('jp-theme', next);
      reflect();
    });
    reflect();
  }

  /* Skip-link target: pages carry id="main" on <main>; guarantee it for any
     page that predates the skip link so "#main" always resolves. */
  function ensureMainId() {
    if (document.getElementById('main')) return;
    var m = document.querySelector('main');
    if (m) m.id = 'main';
  }

  /* Print: <details> cannot be forced open from CSS, so open every closed one
     while printing and restore afterwards (FAQ answers end up on paper). */
  var openedForPrint = [];
  function wirePrint() {
    if (window.__jpPrintWired) return;
    window.__jpPrintWired = true;
    window.addEventListener('beforeprint', function () {
      openedForPrint = [];
      Array.prototype.forEach.call(document.querySelectorAll('details:not([open])'), function (d) {
        d.setAttribute('open', '');
        openedForPrint.push(d);
      });
    });
    window.addEventListener('afterprint', function () {
      openedForPrint.forEach(function (d) { d.removeAttribute('open'); });
      openedForPrint = [];
    });
  }

  function setYear() {
    var y = document.getElementById('year');
    if (y) y.textContent = new Date().getFullYear();
  }

  /* Search: a "Search /" button in the nav plus the "/" shortcut. The overlay
     itself lives in /assets/js/search.js and is injected on first use, so a
     page that is never searched does not download it. Once search.js has
     loaded it owns both triggers (window.jpSearch is set) and this shim
     steps aside. */
  var searchLoading = false;
  function loadSearch() {
    if (window.jpSearch) { window.jpSearch.open(); return; }
    if (searchLoading) return;
    searchLoading = true;
    var s = document.createElement('script');
    s.src = '/assets/js/search.js';
    s.onload = function () { if (window.jpSearch) window.jpSearch.open(); };
    s.onerror = function () { searchLoading = false; };
    document.head.appendChild(s);
  }
  function inTextField(node) {
    if (!node) return false;
    var tag = (node.tagName || '').toLowerCase();
    return tag === 'input' || tag === 'textarea' || tag === 'select' || node.isContentEditable;
  }
  function wireSearch() {
    var nav = document.querySelector('nav.subnav');
    if (nav && !nav.querySelector('[data-search-open]')) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'iconbtn searchbtn';
      btn.setAttribute('data-search-open', '');
      btn.setAttribute('aria-label', 'Search the site (press / anywhere)');
      btn.innerHTML = 'Search <kbd>/</kbd>';
      var theme = document.getElementById('themeBtn');
      if (theme && theme.parentNode === nav) nav.insertBefore(btn, theme);
      else nav.appendChild(btn);
    }
    if (window.__jpSearchWired) return;
    window.__jpSearchWired = true;
    document.addEventListener('click', function (ev) {
      if (window.jpSearch) return;
      var t = ev.target && ev.target.closest ? ev.target.closest('[data-search-open]') : null;
      if (!t) return;
      ev.preventDefault();
      loadSearch();
    });
    document.addEventListener('keydown', function (ev) {
      if (window.jpSearch) return;
      if (ev.key !== '/' || ev.ctrlKey || ev.metaKey || ev.altKey || inTextField(ev.target)) return;
      ev.preventDefault();
      loadSearch();
    });
  }

  function boot() { markActive(); wireSearch(); wireTheme(); setYear(); ensureMainId(); wirePrint(); }

  /* Boot only on partials:loaded. includes.js dispatches it after every
     data-include fetch has settled (success or failure), and every page that
     loads this file also loads includes.js with a data-include slot (checked:
     72 of 72 pages), so a DOMContentLoaded boot would only run once before
     the nav exists and then be repeated here. */
  window.addEventListener('partials:loaded', boot);
})();
