(async function init() {
  const modal = document.getElementById('modeModal');
  modal.innerHTML = await (await fetch('/frontend/mode-selector.html')).text();

  const chatLog = document.getElementById('chatLog');
  const chatForm = document.getElementById('chatForm');
  const prompt = document.getElementById('prompt');
  const sessionId = crypto.randomUUID();

  function bindSocket() {
    GhostSocket.connect(ModeSwitcher.current, {
      onMessage: (data) => {
        if (data.type === 'word' || data.type === 'chunk' || data.type === 'thinking_step') TypingEffect.append(chatLog, data.content || '');
        if (data.type === 'thinking') ThinkingVisualizer.add(data.step);
        if (data.sources) SourceTracker.update(data.sources);
      },
      onReconnect: bindSocket
    });
  }

  modal.addEventListener('click', (e) => {
    const card = e.target.closest('.mode-card');
    if (!card) return;
    ModeSwitcher.apply(card.dataset.mode);
    modal.classList.remove('show');
    bindSocket();
  });

  document.querySelectorAll('.mode-buttons button').forEach((btn) => btn.addEventListener('click', () => { ModeSwitcher.apply(btn.dataset.mode); bindSocket(); }));

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = prompt.value.trim();
    if (!query) return;
    chatLog.textContent += `\n\n👤 ${query}\n🤖 `;
    GhostSocket.send({ query, session_id: sessionId });
    const history = JSON.parse(localStorage.getItem('ghost-history') || '[]');
    history.push({ mode: ModeSwitcher.current, query, at: Date.now() });
    localStorage.setItem('ghost-history', JSON.stringify(history));
    prompt.value = '';
  });

  document.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 'f') ModeSwitcher.apply('fast');
    if (e.key.toLowerCase() === 'p') ModeSwitcher.apply('pro');
    if (e.key.toLowerCase() === 't') ModeSwitcher.apply('thinking');
  });

  ModeSwitcher.apply(ModeSwitcher.current);
})();
