/**
 * Study layer for Janaka Academy content pages (pairs with assets/css/study.css).
 *
 * Adds, without any per-page markup:
 *   - a reading-progress bar
 *   - a meta line under the H1 (reading time, words, sections, code samples)
 *   - a collapsed "how to study this page" note
 *   - section numbers on every H2 and a "mark done" toggle, remembered per page
 *   - an outline card (advance organiser) when a page has three or more sections,
 *     with the active section highlighted and done sections ticked
 *   - a floating "outline · n/m" pill once the reader has scrolled past the outline
 *   - copy buttons on code blocks, and a horizontal-scroll wrapper on wide tables
 *   - a "continue where you left off" prompt when returning to a long page
 *
 * State lives in localStorage under "jp-study:<pathname>" and never leaves the browser.
 * Boots on partials:loaded (see includes.js) so the shared nav exists first.
 */
(function () {
  'use strict';

  var KEY = 'jp-study:' + location.pathname;
  var booted = false;

  function load() { try { return JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { return {}; } }
  function save(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} }

  function slug(t) {
    return (t || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || 'section';
  }
  function text(el) { return (el.textContent || '').replace(/\s+/g, ' ').trim(); }
  function words(el) { return text(el).split(' ').filter(Boolean).length; }
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function throttle(fn, ms) {
    var t = 0, pending = null;
    return function () {
      var now = Date.now();
      if (now - t > ms) { t = now; fn(); }
      else if (!pending) { pending = setTimeout(function () { pending = null; t = Date.now(); fn(); }, ms); }
    };
  }

  function boot() {
    if (booted) return;
    booted = true;
    var main = document.querySelector('main');
    if (!main) return;
    document.body.classList.add('study');

    var state = load();
    state.done = Array.isArray(state.done) ? state.done : [];

    var h1 = main.querySelector('h1') || document.querySelector('h1');   // a few pages keep the hero outside <main>
    var h2s = Array.prototype.slice.call(main.querySelectorAll('h2')).filter(function (h) {
      return !h.closest('.cta') && !h.closest('.study-toc') && text(h).length > 0
        && !/^(on this page|contents|table of contents|outline|browse sections|in this handbook)$/i.test(text(h));
    });

    /* ---- stable ids on every section heading ---- */
    h2s.forEach(function (h) {
      if (h.id) return;
      var base = slug(text(h)), s = base, i = 2;
      while (document.getElementById(s)) s = base + '-' + (i++);
      h.id = s;
    });

    /* ---- progress bar ---- */
    var bar = el('div', 'study-progress');
    document.body.appendChild(bar);
    function paintProgress() {
      var d = document.documentElement;
      var max = d.scrollHeight - window.innerHeight;
      bar.style.width = (max > 0 ? Math.min(100, (window.scrollY / max) * 100) : 0) + '%';
    }

    /* ---- meta line + study note under the H1 ---- */
    var codeBlocks = main.querySelectorAll('pre');
    if (h1 && h1.parentNode) {
      var w = words(main);
      var mins = Math.max(1, Math.round(w / 220));
      var parts = ['<span><b>' + mins + ' min</b> read</span>', '<span><b>' + w.toLocaleString() + '</b> words</span>'];
      if (h2s.length) parts.push('<span><b>' + h2s.length + '</b> sections</span>');
      if (codeBlocks.length) parts.push('<span><b>' + codeBlocks.length + '</b> code samples</span>');
      var meta = el('p', 'study-meta', parts.join(''));
      h1.parentNode.appendChild(meta);

      var how = el('details', 'study-how',
        '<summary><span>How to study this page</span></summary>' +
        '<ol>' +
        '<li><b>Skim the outline first.</b> Knowing the shape of a page before the detail makes the detail easier to hold.</li>' +
        '<li><b>Read one section, then mark it done.</b> Finishing in small closed steps beats one long pass.</li>' +
        '<li><b>Close the page and say it back.</b> Recall what the section claimed before checking. Retrieval is what makes it stick.</li>' +
        '<li><b>Run the code, then change it.</b> Predict the output first, then run it, then break it on purpose.</li>' +
        '<li><b>Come back in a few days.</b> The outline shows what you marked done; re-read only what you cannot recall.</li>' +
        '</ol>');
      h1.parentNode.appendChild(how);
    }

    /* ---- section numbers and done toggles ---- */
    function isDone(id) { return state.done.indexOf(id) >= 0; }
    var tocItems = {};
    function labelFor(pressed) { return pressed ? 'Done ✓' : 'Mark done'; }
    function refreshCounts() {
      var n = h2s.filter(function (h) { return isDone(h.id); }).length;
      var count = document.querySelector('.study-toc .toc-count');
      var fill = document.querySelector('.study-toc .toc-bar i');
      var pill = document.querySelector('.study-pill b');
      if (count) {
        count.textContent = n === h2s.length ? 'All ' + h2s.length + ' done' : n + ' of ' + h2s.length + ' done';
        count.classList.toggle('all', n === h2s.length);
      }
      if (fill) fill.style.width = (h2s.length ? (n / h2s.length) * 100 : 0) + '%';
      if (pill) pill.textContent = n + '/' + h2s.length;
    }
    h2s.forEach(function (h, i) {
      var t = text(h);
      var prev = h.previousElementSibling;
      var alreadyNumbered = /^(\d+|[A-Z])[.)]\s/.test(t) || /^(step|day|part|module)\s+\d/i.test(t)
        || (prev && prev.classList && prev.classList.contains('eyebrow')) || h.closest('.rel-head');
      if (!alreadyNumbered) {
        var n = el('span', 'secnum', String(i + 1).padStart(2, '0'));
        h.insertBefore(n, h.firstChild);
      }
      var b = el('button', 'donebtn', labelFor(isDone(h.id)));
      b.type = 'button';
      b.setAttribute('aria-pressed', isDone(h.id) ? 'true' : 'false');
      b.setAttribute('aria-label', 'Mark section "' + t + '" as done');
      b.addEventListener('click', function () {
        var idx = state.done.indexOf(h.id);
        if (idx >= 0) state.done.splice(idx, 1); else state.done.push(h.id);
        var on = isDone(h.id);
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
        b.textContent = labelFor(on);
        if (tocItems[h.id]) tocItems[h.id].classList.toggle('done', on);
        save(state);
        refreshCounts();
      });
      h.appendChild(b);
      h.classList.add('has-done');
    });

    /* ---- outline card ---- */
    var toc = null;
    var ownToc = main.querySelector('.toc, nav[aria-label*="ontents"]');
    if (h2s.length >= 3 && !ownToc) {
      toc = el('nav', 'study-toc');
      toc.setAttribute('aria-label', 'Page outline');
      toc.innerHTML = '<div class="toc-head"><span>Outline</span><span class="toc-count"></span></div><div class="toc-bar"><i></i></div>';
      var ol = el('ol');
      h2s.forEach(function (h, i) {
        var li = el('li', isDone(h.id) ? 'done' : '');
        var a = el('a');
        a.href = '#' + h.id;
        var label = text(h).replace(/^\d{2}\s*/, '').replace(/\s*(Mark done|Done ✓)$/, '');
        a.innerHTML = '<span class="n">' + String(i + 1).padStart(2, '0') + '</span><span>' + label.replace(/[<>&]/g, function (c) { return { '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]; }) + '</span>';
        li.appendChild(a);
        ol.appendChild(li);
        tocItems[h.id] = li;
      });
      toc.appendChild(ol);

      var section = el('section', 'sec study-toc-sec');
      var wrap = el('div', 'wrap');
      wrap.appendChild(toc);
      section.appendChild(wrap);
      // place it before the top-level block that holds the first section heading
      var anchor = h2s[0];
      while (anchor.parentNode && anchor.parentNode !== main) anchor = anchor.parentNode;
      main.insertBefore(section, anchor);

      var pill = el('a', 'study-pill', 'Outline · <b></b>');
      pill.href = '#';
      pill.addEventListener('click', function (e) { e.preventDefault(); toc.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
      document.body.appendChild(pill);
      var pillEl = pill;

      var links = Array.prototype.slice.call(ol.querySelectorAll('a'));
      function paintActive() {
        var y = window.scrollY + 100, current = null;
        for (var i = 0; i < h2s.length; i++) { if (h2s[i].getBoundingClientRect().top + window.scrollY <= y) current = i; }
        links.forEach(function (a, i) { a.classList.toggle('active', i === current); });
        var past = toc.getBoundingClientRect().bottom < 0;
        pillEl.classList.toggle('show', past);
      }
      window.addEventListener('scroll', throttle(paintActive, 120), { passive: true });
      paintActive();
    }
    refreshCounts();

    /* ---- copy buttons on code blocks ---- */
    Array.prototype.forEach.call(codeBlocks, function (pre) {
      if (pre.querySelector('.copybtn')) return;
      var b = el('button', 'copybtn', 'Copy');
      b.type = 'button';
      b.setAttribute('aria-label', 'Copy code');
      b.addEventListener('click', function () {
        var code = pre.querySelector('code') || pre;
        var t = code.textContent.replace(/\n$/, '');
        var done = function () { b.textContent = 'Copied'; b.classList.add('copied'); setTimeout(function () { b.textContent = 'Copy'; b.classList.remove('copied'); }, 1600); };
        if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, function () {});
        else { var r = document.createRange(); r.selectNodeContents(code); var s = window.getSelection(); s.removeAllRanges(); s.addRange(r); try { document.execCommand('copy'); done(); } catch (e) {} s.removeAllRanges(); }
      });
      pre.appendChild(b);
    });

    /* ---- wide tables scroll instead of breaking the page ---- */
    Array.prototype.forEach.call(main.querySelectorAll('table'), function (t) {
      if (t.closest('.tablewrap')) return;
      var w = el('div', 'tablewrap');
      t.parentNode.insertBefore(w, t);
      w.appendChild(t);
    });

    /* ---- resume where you left off ---- */
    var saveY = throttle(function () {
      state.y = window.scrollY;
      state.at = Date.now();
      save(state);
    }, 1000);
    window.addEventListener('scroll', function () { paintProgress(); saveY(); }, { passive: true });
    paintProgress();

    var pageIsLong = document.documentElement.scrollHeight > window.innerHeight * 2.5;
    if (pageIsLong && state.y > window.innerHeight && window.scrollY < 80 && !location.hash) {
      var toast = el('div', 'study-resume', '<span>Continue where you left off?</span>');
      toast.setAttribute('role', 'status');
      var go = el('button', 'go', 'Continue');
      var no = el('button', '', 'Start over');
      go.addEventListener('click', function () { window.scrollTo({ top: state.y, behavior: 'smooth' }); toast.remove(); });
      no.addEventListener('click', function () { state.y = 0; save(state); toast.remove(); });
      toast.appendChild(go); toast.appendChild(no);
      document.body.appendChild(toast);
      setTimeout(function () { if (toast.parentNode) toast.remove(); }, 12000);
    }
  }

  window.addEventListener('partials:loaded', boot);
  // Safety net for a page that has no data-include slot: boot after the DOM is ready.
  document.addEventListener('DOMContentLoaded', function () { setTimeout(boot, 1200); });
})();
