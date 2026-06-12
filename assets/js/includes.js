/**
 * Simple HTML includes: load partials into any element with data-include="partials/xxx.html".
 * Emits a 'partials:loaded' event on window when all includes finish.
 *
 * IMPORTANT: the partials are pulled in with fetch(), which browsers block on the
 * file:// scheme. If you open index.html by double-clicking it (address bar shows
 * file:///...), none of the sections load and the page comes up nearly empty — the
 * language switch then has almost nothing to translate. Always view through a local
 * server: `python3 -m http.server 8000` then open http://localhost:8000/.
 * When a load fails we surface a banner saying exactly that instead of failing silently.
 */
async function loadPartials() {
  const slots = Array.from(document.querySelectorAll('[data-include]'));
  let failures = 0;
  await Promise.all(
    slots.map(async (el) => {
      const file = el.getAttribute('data-include');
      try {
        const res = await fetch(file, { cache: 'no-cache' });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        el.innerHTML = await res.text();
      } catch (e) {
        failures++;
        console.error('Include failed for', file, e);
      }
    })
  );
  if (failures > 0) showLoadError();
  window.dispatchEvent(new Event('partials:loaded'));
}

/* Visible, friendly explanation when the sections can't be fetched (typically file://). */
function showLoadError() {
  if (document.getElementById('includeError')) return;
  const onFile = location.protocol === 'file:';
  const banner = document.createElement('div');
  banner.id = 'includeError';
  banner.setAttribute('role', 'alert');
  banner.style.cssText =
    'position:fixed;left:0;right:0;top:0;z-index:9999;padding:14px 18px;' +
    'font:500 14px/1.5 system-ui,sans-serif;color:#fff;background:#b42318;' +
    'box-shadow:0 2px 8px rgba(0,0,0,.25);text-align:center';
  banner.innerHTML =
    (onFile
      ? "This page can't load its sections when opened directly from a file. "
      : "This page couldn't load some of its sections. ") +
    'Run a local server and open it over http://: ' +
    '<code style="background:rgba(255,255,255,.2);padding:2px 6px;border-radius:4px">' +
    'python3 -m http.server 8000</code> &rarr; ' +
    '<a href="http://localhost:8000/" style="color:#fff;text-decoration:underline">localhost:8000</a>. ' +
    'Meanwhile, view the <a href="partials/janaka_visual_resume_v3_3.html" ' +
    'style="color:#fff;text-decoration:underline">full visual CV</a>.';
  document.body.appendChild(banner);
}

document.addEventListener('DOMContentLoaded', loadPartials);
