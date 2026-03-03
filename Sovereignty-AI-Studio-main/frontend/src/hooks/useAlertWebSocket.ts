import { useState, useEffect, useCallback, useRef } from 'react';
import { Alert, WebSocketMessage } from '../types/alert';

interface UseAlertWebSocketOptions {
  userId: number;
  apiUrl?: string;
  onAlert?: (alert: Alert) => void;
  onSystemAlert?: (alert: Alert) => void;
  onAlertUpdate?: (alertId: number, action: string) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

export const useAlertWebSocket = ({
  userId,
  apiUrl = 'ws://localhost:9898',
  onAlert,
  onSystemAlert,
  onAlertUpdate,
  autoReconnect = true,
  reconnectInterval = 5000,
}: UseAlertWebSocketOptions) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(`${apiUrl}/api/v1/alerts/ws/${userId}`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);

        ws.addEventListener('close', () => {
          clearInterval(pingInterval);
        });
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          switch (message.type) {
            case 'alert':
              onAlert?.(message.data);
              break;
            case 'system_alert':
              onSystemAlert?.(message.data);
              break;
            case 'alert_update':
              onAlertUpdate?.(message.data.alert_id, message.data.action);
              break;
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Attempt to reconnect if enabled
        if (autoReconnect) {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      setIsConnected(false);
    }
  }, [userId, apiUrl, onAlert, onSystemAlert, onAlertUpdate, autoReconnect, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    connect,
    disconnect,
  };
};
