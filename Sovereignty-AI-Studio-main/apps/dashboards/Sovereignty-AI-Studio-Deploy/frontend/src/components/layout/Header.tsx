import React, { useState, useEffect } from 'react';
import { SparklesIcon, BellIcon } from '@heroicons/react/24/outline';
import { AlertAPI } from '../../services/alertApi';

interface HeaderProps {
  onOpenAlerts: () => void;
}

const Header: React.FC<HeaderProps> = ({ onOpenAlerts }) => {
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    loadUnreadCount();
    // Poll for unread count every 30 seconds
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadUnreadCount = async () => {
    try {
      const stats = await AlertAPI.getAlertStats();
      setUnreadCount(stats.unread);
    } catch (error) {
      console.error('Failed to load unread count:', error);
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <SparklesIcon className="h-8 w-8 text-primary-600" />
            <h1 className="ml-2 text-2xl font-bold text-gray-900 font-space-grotesk">
              Sovereignty AI Studio
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            {/* Alert bell */}
            <button
              onClick={onOpenAlerts}
              className="relative p-2 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="View alerts"
            >
              <BellIcon className="w-6 h-6 text-gray-700" />
              {unreadCount > 0 && (
                <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>
            <button className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors">
              Sign In
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;