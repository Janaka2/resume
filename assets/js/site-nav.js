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
    btn.addEventListener('click', function () {
      var root = document.documentElement;
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      store('jp-theme', next);
    });
  }

  function setYear() {
    var y = document.getElementById('year');
    if (y) y.textContent = new Date().getFullYear();
  }

  function boot() { markActive(); wireTheme(); setYear(); }

  window.addEventListener('partials:loaded', boot);
  document.addEventListener('DOMContentLoaded', boot);
})();
