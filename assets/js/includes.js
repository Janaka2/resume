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
document.addEventListener('DOMContentLoaded', () => {
  const buttons  = document.querySelectorAll('.tab-btn');
  const panels   = document.querySelectorAll('.tab-content');

  function setActive(tabId) {
    // hide all panels
    panels.forEach(p => p.classList.add('hidden'));
    // remove active styles from all buttons
    buttons.forEach(b => b.classList.remove('active','text-blue-600','border-b-2','border-blue-400'));
    // show selected panel
    const panel = document.getElementById(tabId);
    if (panel) panel.classList.remove('hidden');
    // style the selected button
    const btn = Array.from(buttons).find(b => b.dataset.tab === tabId);
    if (btn) btn.classList.add('active','text-blue-600','border-b-2','border-blue-400');
  }

  // default: Education
  setActive('educationJourney');

  // clicks
  buttons.forEach(b => b.addEventListener('click', () => setActive(b.dataset.tab)));
});