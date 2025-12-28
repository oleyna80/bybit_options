import { WebSocketMessage } from '../types';

const WS_URL = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000/ws/portfolio';

type WebSocketCallback = (message: WebSocketMessage) => void;
type ConnectionStatusCallback = (connected: boolean) => void;

interface WebSocketConfig {
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  autoConnect?: boolean;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts: number;
  private reconnectDelay: number;
  private heartbeatIntervalMs: number;
  private messageCallbacks: WebSocketCallback[] = [];
  private statusCallbacks: ConnectionStatusCallback[] = [];
  private isConnecting = false;
  private heartbeatInterval: number | null = null;
  private autoConnect: boolean;
  private connectionId: string = '';
  private lastMessageTime: number = 0;
  private messageQueue: any[] = [];

  constructor(config: WebSocketConfig = {}) {
    this.maxReconnectAttempts = config.maxReconnectAttempts || 10;
    this.reconnectDelay = config.reconnectDelay || 1000;
    this.heartbeatIntervalMs = config.heartbeatInterval || 30000;
    this.autoConnect = config.autoConnect !== false;

    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
    this.handleClose = this.handleClose.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleOpen = this.handleOpen.bind(this);

    if (this.autoConnect) {
      this.connect();
    }
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;
    this.connectionId = `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    console.log(`WebSocket connecting (${this.connectionId})...`);
    
    try {
      this.ws = new WebSocket(WS_URL);
      
      this.ws.onopen = this.handleOpen;
      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error, event.data);
        }
      };
      this.ws.onclose = this.handleClose;
      this.ws.onerror = this.handleError;
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  private handleOpen(): void {
    console.log(`WebSocket connected (${this.connectionId})`);
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.notifyStatusChange(true);
    this.startHeartbeat();
    this.flushMessageQueue();
    
    // Send subscription message for portfolio updates
    this.send({
      type: 'subscribe',
      subscriptions: ['portfolio', 'trade_update', 'options_board_update']
    });
  }

  disconnect(): void {
    console.log(`WebSocket disconnecting (${this.connectionId})...`);
    this.stopHeartbeat();
    this.autoConnect = false;
    
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close(1000, 'Client disconnected');
      this.ws = null;
    }
    
    this.notifyStatusChange(false);
    this.messageQueue = [];
  }

  subscribe(callback: WebSocketCallback): () => void {
    this.messageCallbacks.push(callback);
    return () => {
      this.messageCallbacks = this.messageCallbacks.filter(cb => cb !== callback);
    };
  }

  onStatusChange(callback: ConnectionStatusCallback): () => void {
    this.statusCallbacks.push(callback);
    return () => {
      this.statusCallbacks = this.statusCallbacks.filter(cb => cb !== callback);
    };
  }

  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      this.lastMessageTime = Date.now();
    } else {
      console.warn('WebSocket is not connected, queuing message:', message.type || 'unknown');
      this.messageQueue.push(message);
      
      // Try to reconnect if not already connecting
      if (!this.isConnecting && this.autoConnect) {
        this.connect();
      }
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getConnectionId(): string {
    return this.connectionId;
  }

  getStats() {
    return {
      connected: this.isConnected(),
      connecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      maxReconnectAttempts: this.maxReconnectAttempts,
      messageCallbacks: this.messageCallbacks.length,
      statusCallbacks: this.statusCallbacks.length,
      messageQueueLength: this.messageQueue.length,
      lastMessageTime: this.lastMessageTime,
      connectionId: this.connectionId,
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    // Handle heartbeat responses
    if ((message as any).type === 'pong') {
      return;
    }
    
    // Update last message time
    this.lastMessageTime = Date.now();
    
    // Notify all subscribers
    this.messageCallbacks.forEach(callback => {
      try {
        callback(message);
      } catch (error) {
        console.error('Error in WebSocket callback:', error);
      }
    });
  }

  private handleClose(event: CloseEvent): void {
    console.log(`WebSocket disconnected (${this.connectionId}):`, event.code, event.reason);
    this.isConnecting = false;
    this.stopHeartbeat();
    this.notifyStatusChange(false);
    
    // Don't reconnect if closed normally or by client
    if (event.code === 1000 || !this.autoConnect) {
      console.log('WebSocket closed normally, not reconnecting');
      return;
    }
    
    // Schedule reconnect with exponential backoff
    this.scheduleReconnect();
  }

  private handleError(event: Event): void {
    console.error(`WebSocket error (${this.connectionId}):`, event);
    this.isConnecting = false;
    this.notifyStatusChange(false);
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn(`Max reconnection attempts (${this.maxReconnectAttempts}) reached`);
      this.notifyStatusChange(false);
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (!this.isConnected() && !this.isConnecting && this.autoConnect) {
        this.connect();
      }
    }, delay);
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        // Check if we've received messages recently
        const timeSinceLastMessage = Date.now() - this.lastMessageTime;
        if (timeSinceLastMessage > this.heartbeatIntervalMs * 2) {
          console.log('No messages received recently, sending ping');
          this.send({ type: 'ping', timestamp: new Date().toISOString() });
        }
      }
    }, this.heartbeatIntervalMs);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private flushMessageQueue(): void {
    if (this.messageQueue.length > 0 && this.isConnected()) {
      console.log(`Flushing ${this.messageQueue.length} queued messages`);
      const queue = [...this.messageQueue];
      this.messageQueue = [];
      
      queue.forEach(message => {
        this.send(message);
      });
    }
  }

  protected notifyStatusChange(connected: boolean): void {
    this.statusCallbacks.forEach(callback => {
      try {
        callback(connected);
      } catch (error) {
        console.error('Error in status callback:', error);
      }
    });
  }
}


// Всегда использовать реальный WebSocket клиент
const wsClient = new WebSocketClient();
export default wsClient;