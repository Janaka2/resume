
function copyText(id){
  const el = document.getElementById(id);
  if(!el) return;
  navigator.clipboard.writeText(el.innerText).then(() => {
    const btn = document.querySelector('[data-copy="'+id+'"]');
    if(btn){
      const old = btn.innerText;
      btn.innerText = 'Copied';
      setTimeout(() => btn.innerText = old, 1200);
    }
  });
}
