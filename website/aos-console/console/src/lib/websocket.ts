type MessageHandler = (data: unknown) => void;

export class WebSocketConnection {
  private ws: WebSocket | null = null;
  private subscriptions: Set<string> = new Set();
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private token = '';
  private url = '';

  connect(url: string, token: string) {
    this.url = url;
    this.token = token;
    const fullUrl = `${url}?token=${token}`;
    this.ws = new WebSocket(fullUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.subscriptions.forEach((channel) => this.subscribe(channel));
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      if (!event.wasClean) {
        this.reconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  subscribe(channel: string) {
    this.subscriptions.add(channel);
    this.send({ type: 'subscribe', channel });
  }

  unsubscribe(channel: string) {
    this.subscriptions.delete(channel);
    this.send({ type: 'unsubscribe', channel });
  }

  on(eventType: string, handler: MessageHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);
  }

  off(eventType: string, handler: MessageHandler) {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private send(data: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private handleMessage(message: { type: string; event?: unknown; channel?: string }) {
    if (message.type === 'event' && message.event) {
      const handlers = this.handlers.get('event') || [];
      handlers.forEach((handler) => handler(message.event));
    }
    if (message.type === 'ack') {
      console.log('Subscribed to:', message.channel);
    }
  }

  private reconnect() {
    if (this.reconnectAttempts >= 10) return;

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(this.url, this.token);
    }, delay);
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
    this.subscriptions.clear();
    this.handlers.clear();
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsConnection = new WebSocketConnection();
