type EventHandler = (event: MessageEvent) => void;

export class SSEConnection {
  private eventSource: EventSource | null = null;
  private handlers: Map<string, EventHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseDelay = 1000;
  private url = '';
  private token = '';

  connect(url: string, token: string) {
    this.url = url;
    this.token = token;
    const fullUrl = `${url}?token=${token}`;
    this.eventSource = new EventSource(fullUrl);

    this.eventSource.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.eventSource.onerror = () => {
      this.reconnect();
    };

    this.eventSource.onmessage = (event) => {
      const handlers = this.handlers.get('message') || [];
      handlers.forEach((handler) => handler(event));
    };
  }

  on(eventType: string, handler: EventHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, []);
    }
    this.handlers.get(eventType)!.push(handler);

    if (this.eventSource && eventType !== 'message') {
      this.eventSource.addEventListener(eventType, handler);
    }
  }

  off(eventType: string, handler: EventHandler) {
    const handlers = this.handlers.get(eventType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('SSE: Max reconnection attempts reached');
      return;
    }

    const delay = Math.min(
      this.baseDelay * Math.pow(2, this.reconnectAttempts),
      30000
    );

    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect(this.url, this.token);
    }, delay);
  }

  disconnect() {
    this.eventSource?.close();
    this.eventSource = null;
    this.handlers.clear();
  }

  get isConnected(): boolean {
    return this.eventSource?.readyState === EventSource.OPEN;
  }
}

export const jobSSE = new SSEConnection();
export const messageSSE = new SSEConnection();
