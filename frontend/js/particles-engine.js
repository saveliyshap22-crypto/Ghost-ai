window.ParticlesEngine = {
  start(mode) {
    const c = document.getElementById('particles');
    const ctx = c.getContext('2d');
    const colors = { fast: '#00ff88', pro: '#6c63ff', thinking: '#00d4ff' };
    c.width = innerWidth; c.height = innerHeight;
    const count = mode === 'thinking' ? 45 : mode === 'pro' ? 35 : 25;
    const dots = Array.from({ length: count }, () => ({ x: Math.random()*c.width, y: Math.random()*c.height, v: Math.random()*1.2+0.2 }));
    cancelAnimationFrame(this.raf);
    const draw = () => {
      ctx.clearRect(0,0,c.width,c.height); ctx.fillStyle = colors[mode];
      dots.forEach(d => { d.y += d.v; if (d.y > c.height) d.y = -10; ctx.beginPath(); ctx.arc(d.x, d.y, 2, 0, Math.PI*2); ctx.fill(); });
      this.raf = requestAnimationFrame(draw);
    };
    draw();
  }
};
