import React, { useState, useEffect, useCallback } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import AlertCenter from '../alerts/AlertCenter';
import AlertContainer from '../alerts/AlertContainer';
import { useAlertWebSocket } from '../../hooks/useAlertWebSocket';
import { Alert } from '../../types/alert';
import { AlertAPI } from '../../services/alertApi';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [alertCenterOpen, setAlertCenterOpen] = useState(false);
  const [toastAlerts, setToastAlerts] = useState<Alert[]>([]);
  
  // For demo purposes, using userId 1. In production, get from auth context
  const userId = 1;

  // Handle new alerts from WebSocket
  const handleNewAlert = useCallback((alert: Alert) => {
    console.log('New alert received:', alert);
    // Add to toast notifications (show for 5-10 seconds)
    setToastAlerts(prev => [alert, ...prev].slice(0, 5)); // Keep max 5 toasts
  }, []);

  const handleSystemAlert = useCallback((alert: Alert) => {
    console.log('System alert received:', alert);
    // System alerts are shown as toasts
    setToastAlerts(prev => [alert, ...prev].slice(0, 5));
  }, []);

  const handleAlertUpdate = useCallback((alertId: number, action: string) => {
    console.log(`Alert ${alertId} updated: ${action}`);
    // Remove from toast if dismissed
    if (action === 'dismissed') {
      setToastAlerts(prev => prev.filter(a => a.id !== alertId));
    }
  }, []);

  // Initialize WebSocket connection
  const { isConnected } = useAlertWebSocket({
    userId,
    apiUrl: process.env.REACT_APP_WS_URL || 'ws://localhost:9898',
    onAlert: handleNewAlert,
    onSystemAlert: handleSystemAlert,
    onAlertUpdate: handleAlertUpdate,
    autoReconnect: true,
  });

  const handleDismissToast = async (alertId: number) => {
    try {
      await AlertAPI.dismissAlert(alertId);
      setToastAlerts(prev => prev.filter(a => a.id !== alertId));
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
    }
  };

  const handleMarkToastAsRead = async (alertId: number) => {
    try {
      await AlertAPI.markAsRead(alertId);
      setToastAlerts(prev =>
        prev.map(a => (a.id === alertId ? { ...a, is_read: true } : a))
      );
    } catch (error) {
      console.error('Failed to mark alert as read:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header onOpenAlerts={() => setAlertCenterOpen(true)} />
      {/* WebSocket connection indicator */}
      {!isConnected && (
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
            ⚠️ Live alerts disconnected. Reconnecting...
          </div>
        </div>
      )}
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
      
      {/* Alert Center (slide-out panel) */}
      <AlertCenter
        isOpen={alertCenterOpen}
        onClose={() => setAlertCenterOpen(false)}
      />
      
      {/* Toast Notifications */}
      <AlertContainer
        alerts={toastAlerts}
        onDismiss={handleDismissToast}
        onRead={handleMarkToastAsRead}
        position="top-right"
      />
    </div>
  );
};

export default Layout;