// useWebSocket: React hook for subscribing to WebSocket events
import { useEffect, useRef } from 'react';
import { websocketService, WebSocketEvent } from '../services/websocket';
import { getAuthToken } from '../services/auth';

export function useWebSocket(event: WebSocketEvent, onMessage: (data: any) => void) {
  const isConnected = useRef(false);

  useEffect(() => {
    if (!isConnected.current) {
      const token = getAuthToken();
      if (token) {
        websocketService.connect(token);
        isConnected.current = true;
      }
    }
    websocketService.on(event, onMessage);
    return () => {
      websocketService.disconnect();
      isConnected.current = false;
    };
  }, [event, onMessage]);
}
