function initAOS() {
  if (window.AOS) AOS.init({ duration: 800, easing: 'ease-in-out', once: true });
}
function initVanta() {
  if (window.VANTA && document.getElementById('vanta-bg')) {
    VANTA.GLOBE({
      el: "#vanta-bg",
      mouseControls: true, touchControls: true, gyroControls: false,
      minHeight: 200.00, minWidth: 200.00, scale: 1.00, scaleMobile: 1.00,
      color: 0x3b82f6, backgroundColor: 0xf8fafc, size: 0.8
    });
  }
}
function initFeather() { if (window.feather) feather.replace(); }

// Tabs
function setupTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  if (!tabBtns.length || !tabContents.length) return;
  tabBtns[0].classList.add('active');
  tabContents[0].classList.remove('hidden');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      const tabId = this.getAttribute('data-tab');
      tabBtns.forEach(b => b.classList.remove('active'));
      tabContents.forEach(c => c.classList.add('hidden'));
      this.classList.add('active');
      const target = document.getElementById(tabId);
      if (target) target.classList.remove('hidden');
    });
  });
}

// Collapsibles (Work History)
function setupWorkHistory() {
  const content = document.getElementById('workHistoryContent');
  const chevron = document.getElementById('workHistoryChevron');
  const toggleBtn = document.getElementById('toggleLongHistory');
  if (!content) return;

  window.toggleWorkHistory = function() {
    if (content.style.maxHeight) { content.style.maxHeight = null; chevron && (chevron.style.transform = 'rotate(0deg)'); }
    else { content.style.maxHeight = content.scrollHeight + "px"; chevron && (chevron.style.transform = 'rotate(180deg)'); }
  };
  window.showWorkHistory = function() {
    content.style.maxHeight = content.scrollHeight + "px";
    chevron && (chevron.style.transform = 'rotate(180deg)');
    content.scrollIntoView({ behavior: 'smooth' });
  };
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      const longHistory = document.getElementById('longHistory');
      const container = document.getElementById('workHistoryContent');
      const willOpen = longHistory.classList.contains('hidden');
      if (willOpen) longHistory.classList.remove('hidden'); else longHistory.classList.add('hidden');
      requestAnimationFrame(() => { container.style.maxHeight = container.scrollHeight + 'px'; });
      this.textContent = willOpen ? 'Show less' : 'Read more';
    });
  }
  window.showAllCertifications = function() {
    const el = document.getElementById('certifications'); el && el.scrollIntoView({ behavior: 'smooth' });
  };
  window.showEducationDetails = function() {
    const el = document.getElementById('education'); el && el.scrollIntoView({ behavior: 'smooth' });
  };
}

// Chat popup
function setupChatPopup() {
  window.openChatPopup = function() {
    const el = document.getElementById('chatPopup');
    if (el) { el.classList.remove('hidden'); document.body.style.overflow = 'hidden'; }
  }
  window.closeChatPopup = function() {
    const el = document.getElementById('chatPopup');
    if (el) { el.classList.add('hidden'); document.body.style.overflow = 'auto'; }
  }
}

// Bootstrap everything *after* partials are loaded
window.addEventListener('partials:loaded', () => {
  initAOS();
  initVanta();
  initFeather();
  setupTabs();
  setupWorkHistory();
  setupChatPopup();
});
