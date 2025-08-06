import React, { createContext, useContext, useEffect, useState } from 'react';
import io from 'socket.io-client';
import { useAuth } from './AuthContext';

const SocketContext = createContext({});

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [realTimeData, setRealTimeData] = useState({});
  const { isAuthenticated, accessToken } = useAuth();

  useEffect(() => {
    if (isAuthenticated && accessToken) {
      initializeSocket();
    } else {
      disconnectSocket();
    }

    return () => {
      disconnectSocket();
    };
  }, [isAuthenticated, accessToken]);

  const initializeSocket = () => {
    try {
      const socketUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
      
      const newSocket = io(socketUrl, {
        auth: {
          token: accessToken
        },
        transports: ['websocket', 'polling'],
        upgrade: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      });

      newSocket.on('connect', () => {
        console.log('Socket connected:', newSocket.id);
        setConnected(true);
      });

      newSocket.on('disconnect', () => {
        console.log('Socket disconnected');
        setConnected(false);
      });

      newSocket.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
        setConnected(false);
      });

      // Listen for real-time data updates
      newSocket.on('device_data', (data) => {
        setRealTimeData(prev => ({
          ...prev,
          [data.device_id]: data
        }));
      });

      newSocket.on('device_status', (status) => {
        setRealTimeData(prev => ({
          ...prev,
          [`${status.device_id}_status`]: status
        }));
      });

      newSocket.on('alert', (alert) => {
        // Handle real-time alerts
        console.log('Real-time alert:', alert);
      });

      newSocket.on('system_notification', (notification) => {
        // Handle system notifications
        console.log('System notification:', notification);
      });

      setSocket(newSocket);
    } catch (error) {
      console.error('Socket initialization error:', error);
    }
  };

  const disconnectSocket = () => {
    if (socket) {
      socket.disconnect();
      setSocket(null);
      setConnected(false);
      setRealTimeData({});
    }
  };

  const emit = (event, data) => {
    if (socket && connected) {
      socket.emit(event, data);
    }
  };

  const subscribe = (event, callback) => {
    if (socket) {
      socket.on(event, callback);
      
      // Return unsubscribe function
      return () => {
        socket.off(event, callback);
      };
    }
  };

  const value = {
    socket,
    connected,
    realTimeData,
    emit,
    subscribe,
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
};
