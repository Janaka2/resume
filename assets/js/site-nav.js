/**
 * Marks the current section in partials/site-nav.html.
 * The nav ships with no active state; the section is derived from the URL,
 * so one file serves every sub-site. Runs after includes.js fires
 * 'partials:loaded', and again on DOMContentLoaded for statically embedded navs.
 */
(function () {
  'use strict';

  var ON = ['text-indigo-600', 'font-semibold', 'border-b-2', 'border-indigo-600'];

  function sectionFromPath() {
    var seg = location.pathname.split('/')[1] || '';
    return seg.toLowerCase().replace(/\.html$/, '') || 'home';
  }

  function mark() {
    var links = document.querySelectorAll('[data-nav]');
    if (!links.length) return;
    var here = sectionFromPath();
    Array.prototype.forEach.call(links, function (a) {
      var active = a.getAttribute('data-nav') === here;
      ON.forEach(function (c) { a.classList.toggle(c, active); });
      a.classList.toggle('text-blue-600', !active);
      if (active) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
  }

  window.addEventListener('partials:loaded', mark);
  document.addEventListener('DOMContentLoaded', mark);
})();
