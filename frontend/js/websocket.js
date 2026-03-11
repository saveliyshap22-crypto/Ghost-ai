window.GhostSocket = {
  ws: null,
  connect(mode, handlers) {
    if (this.ws) this.ws.close();
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    this.ws = new WebSocket(`${proto}://${location.host}/ws/chat/${mode}`);
    this.ws.onmessage = (e) => handlers.onMessage(JSON.parse(e.data));
    this.ws.onclose = () => setTimeout(() => handlers.onReconnect?.(), 1200);
    return this.ws;
  },
  send(payload) { this.ws?.send(JSON.stringify(payload)); }
};
