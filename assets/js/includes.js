/**
 * Simple HTML includes: load partials into any element with data-include="partials/xxx.html".
 * Emits a 'partials:loaded' event on window when all includes finish.
 * (Needs to be served over http(s) — fetch() does not work from file://.)
 */
async function loadPartials() {
  const slots = Array.from(document.querySelectorAll('[data-include]'));
  await Promise.all(
    slots.map(async (el) => {
      const file = el.getAttribute('data-include');
      // Slots pre-filled at build time (scripts/build-hub.py) are left alone.
      if (el.hasAttribute('data-inlined')) return;
      try {
        const res = await fetch(file, { cache: 'no-cache' });
        el.innerHTML = await res.text();
      } catch (e) {
        console.error('Include failed for', file, e);
      }
    })
  );
  window.dispatchEvent(new Event('partials:loaded'));
}
document.addEventListener('DOMContentLoaded', loadPartials);

/*
 * WebMCP: expose the site's read-only tools to in-browser AI agents
 * (assets/js/agent/, docs/ai/webmcp.md). Progressive enhancement: the adapter
 * is fetched only when the browser exposes the API, so every other visitor
 * pays one property check. Chrome needs an origin-trial token for janaka.me;
 * paste it into WEBMCP_OT_TOKEN (empty = only browsers with the flag on).
 */
(function () {
  var WEBMCP_OT_TOKEN = '';
  try {
    if (WEBMCP_OT_TOKEN && !document.querySelector('meta[http-equiv="origin-trial"]')) {
      var m = document.createElement('meta');
      m.httpEquiv = 'origin-trial';
      m.content = WEBMCP_OT_TOKEN;
      document.head.appendChild(m);
    }
    if (document.modelContext && window.isSecureContext) {
      import('/assets/js/agent/webmcp.js')
        .then(function (mod) { mod.start(window); })
        .catch(function (e) { console.warn('[webmcp] adapter unavailable', e); });
    }
  } catch (e) { /* never let an optional feature break the page */ }
})();
