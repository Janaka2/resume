
function filterNav(){
  const value = document.getElementById('searchBox').value.toLowerCase().trim();
  const items = document.querySelectorAll('[data-nav-item]');
  items.forEach(item => {
    const text = item.innerText.toLowerCase();
    item.style.display = text.includes(value) ? '' : 'none';
  });
}
