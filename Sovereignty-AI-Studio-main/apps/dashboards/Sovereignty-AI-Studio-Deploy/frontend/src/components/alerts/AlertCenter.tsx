import React, { useState, useEffect } from 'react';
import { Alert } from '../../types/alert';
import { AlertAPI } from '../../services/alertApi';
import { BellIcon, CheckIcon, TrashIcon } from '@heroicons/react/24/outline';
import AlertNotification from './AlertNotification';

interface AlertCenterProps {
  isOpen: boolean;
  onClose: () => void;
}

const AlertCenter: React.FC<AlertCenterProps> = ({ isOpen, onClose }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  useEffect(() => {
    if (isOpen) {
      loadAlerts();
    }
  }, [isOpen, filter]);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const fetchedAlerts = await AlertAPI.getAlerts({
        unread_only: filter === 'unread',
        limit: 50,
      });
      setAlerts(fetchedAlerts);
    } catch (error) {
      console.error('Failed to load alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (alertId: number) => {
    try {
      await AlertAPI.markAsRead(alertId);
      setAlerts(alerts.map(a => 
        a.id === alertId ? { ...a, is_read: true } : a
      ));
    } catch (error) {
      console.error('Failed to mark alert as read:', error);
    }
  };

  const handleDismiss = async (alertId: number) => {
    try {
      await AlertAPI.dismissAlert(alertId);
      setAlerts(alerts.filter(a => a.id !== alertId));
    } catch (error) {
      console.error('Failed to dismiss alert:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    const unreadIds = alerts.filter(a => !a.is_read).map(a => a.id);
    if (unreadIds.length === 0) return;

    try {
      await AlertAPI.markMultipleAsRead(unreadIds);
      setAlerts(alerts.map(a => ({ ...a, is_read: true })));
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-25 transition-opacity"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className="fixed inset-y-0 right-0 max-w-full flex">
        <div className="w-screen max-w-md">
          <div className="h-full flex flex-col bg-white shadow-xl">
            {/* Header */}
            <div className="px-4 py-6 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <BellIcon className="w-6 h-6" />
                  <h2 className="text-xl font-semibold">Alerts</h2>
                </div>
                <button
                  onClick={onClose}
                  className="text-white hover:text-gray-200 focus:outline-none"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Filter tabs */}
              <div className="mt-4 flex space-x-2">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === 'all'
                      ? 'bg-white text-blue-700'
                      : 'bg-blue-500 text-white hover:bg-blue-400'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => setFilter('unread')}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    filter === 'unread'
                      ? 'bg-white text-blue-700'
                      : 'bg-blue-500 text-white hover:bg-blue-400'
                  }`}
                >
                  Unread
                </button>
              </div>
            </div>

            {/* Actions */}
            {alerts.some(a => !a.is_read) && (
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                <button
                  onClick={handleMarkAllAsRead}
                  className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-800"
                >
                  <CheckIcon className="w-4 h-4" />
                  <span>Mark all as read</span>
                </button>
              </div>
            )}

            {/* Alerts list */}
            <div className="flex-1 overflow-y-auto p-4">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : alerts.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-gray-500">
                  <BellIcon className="w-12 h-12 mb-2 text-gray-300" />
                  <p>No alerts</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {alerts.map(alert => (
                    <div
                      key={alert.id}
                      className={`rounded-lg border p-4 transition-colors ${
                        alert.is_read ? 'bg-white border-gray-200' : 'bg-blue-50 border-blue-200'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-gray-900">{alert.title}</p>
                          <p className="mt-1 text-sm text-gray-600">{alert.message}</p>
                          <p className="mt-2 text-xs text-gray-400">
                            {new Date(alert.created_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="ml-3 flex space-x-1">
                          {!alert.is_read && (
                            <button
                              onClick={() => handleMarkAsRead(alert.id)}
                              className="p-1 rounded hover:bg-gray-200"
                              title="Mark as read"
                            >
                              <CheckIcon className="w-4 h-4 text-gray-600" />
                            </button>
                          )}
                          <button
                            onClick={() => handleDismiss(alert.id)}
                            className="p-1 rounded hover:bg-gray-200"
                            title="Dismiss"
                          >
                            <TrashIcon className="w-4 h-4 text-gray-600" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlertCenter;
