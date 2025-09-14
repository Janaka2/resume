/**
 * Simple HTML includes: load partials into any element with data-include="partials/xxx.html".
 * Emits a 'partials:loaded' event on window when all includes finish.
 */
async function loadPartials() {
  const slots = Array.from(document.querySelectorAll('[data-include]'));
  await Promise.all(
    slots.map(async (el) => {
      const file = el.getAttribute('data-include');
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
