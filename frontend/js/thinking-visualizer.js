window.ThinkingVisualizer = {
  add(step) {
    const panel = document.getElementById('thinkingPanel');
    const node = document.createElement('div');
    node.className = 'thinking-step';
    node.innerHTML = `<strong>${step.stage || 'step'}</strong><div>${step.thought || ''}</div>`;
    panel.prepend(node);
  },
  export() {
    const text = [...document.querySelectorAll('.thinking-step')].map((x) => x.innerText).join('\n\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'ghostai-thinking.txt';
    a.click();
  }
};
