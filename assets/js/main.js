/**
 * Main page behaviour: theme switch, EN/DE language switch, tabs,
 * collapsible work history, chat popup. Plain JS, no dependencies.
 * Everything boots after the partials have been injected (partials:loaded).
 */
(function () {
  'use strict';

  function getStore(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function setStore(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  var STR = window.JP_I18N.STR;

  /* ---------- language state (shared key with the visual CV page) ---------- */
  var lang = getStore('jp-lang');
  if (lang !== 'en' && lang !== 'de') {
    lang = ((navigator.language || '').toLowerCase().indexOf('de') === 0) ? 'de' : 'en';
  }

  /* ---------- theme (initial value is set pre-paint in <head>) ---------- */
  function setupTheme() {
    var root = document.documentElement;
    var themeBtn = document.getElementById('themeBtn');
    if (!themeBtn) return;
    function reflect() {
      themeBtn.setAttribute('aria-pressed', root.getAttribute('data-theme') === 'dark' ? 'true' : 'false');
    }
    themeBtn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      setStore('jp-theme', next);
      reflect();
    });
    reflect();
  }

  /* ---------- language ---------- */
  function applyLang() {
    document.documentElement.setAttribute('lang', lang);
    document.title = STR[lang].title;
    window.JP_I18N.apply(lang);

    var langBtn = document.getElementById('langBtn');
    if (langBtn) {
      langBtn.textContent = (lang === 'en') ? 'DE' : 'EN';
      langBtn.setAttribute('aria-label', STR[lang].langBtnAria);
    }
    var themeBtn = document.getElementById('themeBtn');
    if (themeBtn) themeBtn.setAttribute('aria-label', STR[lang].themeBtnAria);

    /* language-aware PDF link */
    var pdfBtn = document.getElementById('pdfBtn');
    if (pdfBtn) pdfBtn.setAttribute('href', STR[lang].pdf);

    /* "Read more" button label depends on its open/closed state */
    var longHistory = document.getElementById('longHistory');
    var toggleBtn = document.getElementById('toggleLongHistory');
    if (toggleBtn && longHistory) {
      toggleBtn.textContent = longHistory.classList.contains('hidden') ? STR[lang].readMore : STR[lang].showLess;
    }
    var chatClose = document.querySelector('#chatPopup .modal-close');
    if (chatClose) chatClose.setAttribute('aria-label', STR[lang].chatClose);

    /* translated text can change heights: refresh the open collapsible */
    var content = document.getElementById('workHistoryContent');
    if (content && content.style.maxHeight) {
      content.style.maxHeight = content.scrollHeight + 'px';
    }
  }
  function setupLang() {
    var langBtn = document.getElementById('langBtn');
    if (!langBtn) return;
    langBtn.addEventListener('click', function () {
      lang = (lang === 'en') ? 'de' : 'en';
      setStore('jp-lang', lang);
      applyLang();
    });
  }

  /* ---------- footer year ---------- */
  function setupYear() {
    var y = document.getElementById('year');
    if (y) y.textContent = new Date().getFullYear();
  }

  /* ---------- life journey tabs ---------- */
  function setupTabs() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.tab-btn'));
    var panels = Array.prototype.slice.call(document.querySelectorAll('.tab-content'));
    if (!buttons.length || !panels.length) return;

    /* WAI-ARIA tabs pattern: role="tablist" on the bar, role="tab" buttons with a
       roving tabindex, role="tabpanel" panes. The markup in
       partials/life-journey-tabs.html already carries the roles/ids; the
       attributes are (re)asserted here so the partial and the script cannot drift. */
    var bar = buttons[0].parentNode;
    if (bar) bar.setAttribute('role', 'tablist');
    buttons.forEach(function (b) {
      var panelId = b.dataset.tab;
      if (!b.id) b.id = 'tab-' + panelId;
      b.setAttribute('role', 'tab');
      b.setAttribute('aria-controls', panelId);
      b.removeAttribute('aria-pressed');
    });
    panels.forEach(function (p) {
      p.setAttribute('role', 'tabpanel');
      p.setAttribute('tabindex', '0');
      var tab = buttons.filter(function (b) { return b.dataset.tab === p.id; })[0];
      if (tab) p.setAttribute('aria-labelledby', tab.id);
    });

    function setActive(tabId, focusTab) {
      panels.forEach(function (p) { p.classList.toggle('hidden', p.id !== tabId); });
      buttons.forEach(function (b) {
        var on = b.dataset.tab === tabId;
        b.classList.toggle('active', on);
        b.setAttribute('aria-selected', on ? 'true' : 'false');
        b.setAttribute('tabindex', on ? '0' : '-1');
        if (on && focusTab) b.focus();
      });
    }
    buttons.forEach(function (b, i) {
      b.addEventListener('click', function () { setActive(b.dataset.tab); });
      b.addEventListener('keydown', function (ev) {
        var next;
        switch (ev.key) {
          case 'ArrowRight': next = (i + 1) % buttons.length; break;
          case 'ArrowLeft':  next = (i - 1 + buttons.length) % buttons.length; break;
          case 'Home':       next = 0; break;
          case 'End':        next = buttons.length - 1; break;
          default: return;
        }
        ev.preventDefault();
        setActive(buttons[next].dataset.tab, true);
      });
    });
    setActive('educationJourney'); // default tab, as before
  }

  /* ---------- collapsible work history ---------- */
  function setupWorkHistory() {
    var content = document.getElementById('workHistoryContent');
    var chevron = document.getElementById('workHistoryChevron');
    var head = document.querySelector('#workHistory .fold-head');
    var toggleBtn = document.getElementById('toggleLongHistory');
    if (!content) return;

    function setOpen(open) {
      content.style.maxHeight = open ? content.scrollHeight + 'px' : null;
      if (chevron) chevron.style.transform = open ? 'rotate(180deg)' : 'rotate(0deg)';
      if (head) head.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    window.toggleWorkHistory = function () { setOpen(!content.style.maxHeight); };
    window.showWorkHistory = function () {
      setOpen(true);
      content.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    };

    if (toggleBtn) {
      toggleBtn.addEventListener('click', function () {
        var longHistory = document.getElementById('longHistory');
        if (!longHistory) return;
        var willOpen = longHistory.classList.contains('hidden');
        longHistory.classList.toggle('hidden', !willOpen);
        this.textContent = willOpen ? STR[lang].showLess : STR[lang].readMore;
        requestAnimationFrame(function () {
          if (content.style.maxHeight) content.style.maxHeight = content.scrollHeight + 'px';
        });
      });
    }
  }

  /* ---------- chat popup ---------- */
  var SPACE_ORIGIN = 'https://janaka2-claritybot.hf.space';
  var WAKE_TIMEOUT_MS = 45000;

  function setupChatPopup() {
    var popup = document.getElementById('chatPopup');
    var lastFocus = null;
    var inerted = [];
    var warmed = false;
    var wakeTimer = null;
    var loaded = false;

    /* Warm-up: the Space sleeps after 48h idle. Ping it once on the first
       hover/focus/touch of any trigger so it starts waking before the click. */
    function warmUp() {
      if (warmed) return;
      warmed = true;
      try {
        fetch(SPACE_ORIGIN + '/config', { mode: 'cors', cache: 'no-store' }).catch(function () {});
      } catch (e) {}
    }
    Array.prototype.forEach.call(document.querySelectorAll('[onclick*="openChatPopup"]'), function (el) {
      ['pointerenter', 'focus', 'touchstart'].forEach(function (evt) {
        el.addEventListener(evt, warmUp, { once: true, passive: true });
      });
    });

    /* Focus trap: make everything outside the dialog inert (unfocusable and
       hidden from assistive tech) while it is open. The popup may be nested in
       an include slot, so its ancestors up to <body> are left alone. */
    function setInert(on) {
      if (on) {
        var keep = [];
        for (var n = popup; n && n !== document.body; n = n.parentNode) keep.push(n);
        Array.prototype.forEach.call(document.body.children, function (el) {
          if (keep.indexOf(el) !== -1 || el.hasAttribute('inert')) return;
          el.setAttribute('inert', '');
          inerted.push(el);
        });
      } else {
        inerted.forEach(function (el) { el.removeAttribute('inert'); });
        inerted = [];
      }
    }

    /* Loading state: skeleton overlays the iframe until its "load" fires.
       After 45s without load the waking text becomes a "taking longer" notice;
       the fallback card (email / WhatsApp / CV) stays visible either way. */
    var skeleton = document.getElementById('chatSkeleton');
    var wakeMsg = document.getElementById('chatWakeMsg');
    var foot = document.getElementById('chatFoot');
    var preferBtn = document.getElementById('chatPreferEmail');

    function onIframeLoaded() {
      loaded = true;
      if (wakeTimer) { clearTimeout(wakeTimer); wakeTimer = null; }
      if (skeleton) { skeleton.classList.add('loaded'); skeleton.classList.add('hidden'); }
      if (foot) foot.classList.remove('hidden');
      if (preferBtn) preferBtn.setAttribute('aria-expanded', 'false');
    }
    function onWakeTimeout() {
      wakeTimer = null;
      if (loaded || !wakeMsg) return;
      /* swap the key, seed the English text, then let i18n pick the language */
      wakeMsg.setAttribute('data-i18n', 'chatSlow');
      wakeMsg.textContent = STR.en.chatSlow;
      window.JP_I18N.apply(lang);
    }
    function startIframe(iframe) {
      warmUp();
      iframe.addEventListener('load', onIframeLoaded, { once: true });
      iframe.setAttribute('src', iframe.getAttribute('data-src')); // load on first open only
      wakeTimer = setTimeout(onWakeTimeout, WAKE_TIMEOUT_MS);
    }
    if (preferBtn && skeleton) {
      preferBtn.addEventListener('click', function () {
        var show = skeleton.classList.contains('hidden');
        skeleton.classList.toggle('hidden', !show);
        preferBtn.setAttribute('aria-expanded', show ? 'true' : 'false');
      });
    }

    window.openChatPopup = function () {
      if (!popup) return;
      var iframe = document.getElementById('chatIframe');
      if (iframe && !iframe.getAttribute('src')) startIframe(iframe);
      lastFocus = document.activeElement;
      popup.classList.remove('hidden');
      setInert(true);
      document.body.style.overflow = 'hidden';
      var closeBtn = popup.querySelector('.modal-close');
      if (closeBtn) closeBtn.focus();
    };
    window.closeChatPopup = function () {
      if (!popup) return;
      popup.classList.add('hidden');
      setInert(false);
      document.body.style.overflow = '';
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    };
    if (popup) {
      popup.addEventListener('click', function (ev) {
        if (ev.target === popup) window.closeChatPopup(); // click on the backdrop closes
      });
      document.addEventListener('keydown', function (ev) {
        if (ev.key === 'Escape' && !popup.classList.contains('hidden')) window.closeChatPopup();
      });
    }
  }

  /* ---------- print: open every <details> so FAQ answers are on paper ---------- */
  function setupPrint() {
    var opened = [];
    window.addEventListener('beforeprint', function () {
      opened = [];
      Array.prototype.forEach.call(document.querySelectorAll('details:not([open])'), function (d) {
        d.setAttribute('open', '');
        opened.push(d);
      });
    });
    window.addEventListener('afterprint', function () {
      opened.forEach(function (d) { d.removeAttribute('open'); });
      opened = [];
    });
  }

  /* ---------- boot after partials are in the DOM ---------- */
  window.addEventListener('partials:loaded', function () {
    setupTheme();
    setupLang();
    setupYear();
    setupTabs();
    setupWorkHistory();
    setupChatPopup();
    setupPrint();
    applyLang();
  });
})();
