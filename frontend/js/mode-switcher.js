window.ModeSwitcher = {
  current: localStorage.getItem('ghost-mode') || 'fast',
  apply(mode) {
    this.current = mode;
    document.body.classList.remove('mode-fast', 'mode-pro', 'mode-thinking');
    document.body.classList.add(`mode-${mode}`);
    document.getElementById('modeIndicator').textContent = ({fast:'Ghost 1 Fast',pro:'Ghost 1 Pro',thinking:'Ghost 1 Thinking'})[mode];
    localStorage.setItem('ghost-mode', mode);
    ParticlesEngine.start(mode);
    fetch('/api/select-mode', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({mode}) });
  }
};
