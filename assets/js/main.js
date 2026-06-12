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
    themeBtn.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      setStore('jp-theme', next);
    });
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
    var buttons = document.querySelectorAll('.tab-btn');
    var panels = document.querySelectorAll('.tab-content');
    if (!buttons.length || !panels.length) return;

    function setActive(tabId) {
      panels.forEach(function (p) { p.classList.toggle('hidden', p.id !== tabId); });
      buttons.forEach(function (b) {
        var on = b.dataset.tab === tabId;
        b.classList.toggle('active', on);
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
    }
    buttons.forEach(function (b) {
      b.addEventListener('click', function () { setActive(b.dataset.tab); });
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
  function setupChatPopup() {
    var popup = document.getElementById('chatPopup');
    var lastFocus = null;

    window.openChatPopup = function () {
      if (!popup) return;
      var iframe = document.getElementById('chatIframe');
      if (iframe && !iframe.getAttribute('src')) {
        iframe.setAttribute('src', iframe.getAttribute('data-src')); // load on first open only
      }
      lastFocus = document.activeElement;
      popup.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      var closeBtn = popup.querySelector('.modal-close');
      if (closeBtn) closeBtn.focus();
    };
    window.closeChatPopup = function () {
      if (!popup) return;
      popup.classList.add('hidden');
      document.body.style.overflow = 'auto';
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

  /* ---------- boot after partials are in the DOM ---------- */
  window.addEventListener('partials:loaded', function () {
    setupTheme();
    setupLang();
    setupYear();
    setupTabs();
    setupWorkHistory();
    setupChatPopup();
    applyLang();
  });
})();
