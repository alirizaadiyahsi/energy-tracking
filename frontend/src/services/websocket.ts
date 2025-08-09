// WebSocket service for real-time updates (device status, analytics, etc.)
import { WS_BASE_URL } from '../utils/constants';

export type WebSocketEvent = 'device_update' | 'analytics_update' | 'notification';

export class WebSocketService {
  private socket: WebSocket | null = null;
  private listeners: { [event: string]: ((data: any) => void)[] } = {};

  connect(token: string) {
    this.socket = new WebSocket(`${WS_BASE_URL}?token=${token}`);
    this.socket.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      this.emit(msg.event, msg.data);
    };
  }

  on(event: WebSocketEvent, callback: (data: any) => void) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(callback);
  }

  emit(event: string, data: any) {
    (this.listeners[event] || []).forEach(cb => cb(data));
  }

  send(event: string, data: any) {
    this.socket?.send(JSON.stringify({ event, data }));
  }

  disconnect() {
    this.socket?.close();
    this.socket = null;
    this.listeners = {};
  }
}

export const websocketService = new WebSocketService();
