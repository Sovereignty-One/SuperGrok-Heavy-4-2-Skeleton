import React, { useEffect, useState } from 'react';
import { Alert, AlertType } from '../../types/alert';
import { XMarkIcon, ExclamationTriangleIcon, InformationCircleIcon, ShieldExclamationIcon } from '@heroicons/react/24/outline';

interface AlertNotificationProps {
  alert: Alert;
  onDismiss: (id: number) => void;
  onRead: (id: number) => void;
  autoClose?: number; // Auto-close delay in ms (0 = no auto-close)
}

const AlertNotification: React.FC<AlertNotificationProps> = ({
  alert,
  onDismiss,
  onRead,
  autoClose = 5000,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    // Mark as read when displayed
    if (!alert.is_read) {
      onRead(alert.id);
    }

    // Auto-close for non-critical alerts
    if (autoClose > 0 && alert.severity !== 'critical' && alert.severity !== 'high') {
      const timer = setTimeout(() => {
        handleDismiss();
      }, autoClose);

      return () => clearTimeout(timer);
    }
  }, [alert, autoClose, onRead]);

  const handleDismiss = () => {
    setIsLeaving(true);
    setTimeout(() => {
      setIsVisible(false);
      onDismiss(alert.id);
    }, 300); // Animation duration
  };

  if (!isVisible) return null;

  const getAlertStyles = () => {
    const baseStyles = 'rounded-lg shadow-lg p-4 mb-3 flex items-start space-x-3 transition-all duration-300';
    const severityStyles = {
      low: 'bg-blue-50 border-l-4 border-blue-500',
      medium: 'bg-yellow-50 border-l-4 border-yellow-500',
      high: 'bg-orange-50 border-l-4 border-orange-500',
      critical: 'bg-red-50 border-l-4 border-red-600 animate-pulse',
    };

    return `${baseStyles} ${severityStyles[alert.severity] || severityStyles.medium} ${
      isLeaving ? 'opacity-0 translate-x-full' : 'opacity-100'
    }`;
  };

  const getIcon = () => {
    const iconClass = 'w-6 h-6';
    
    if (alert.type === AlertType.SECURITY || alert.severity === 'critical') {
      return <ShieldExclamationIcon className={`${iconClass} text-red-600`} />;
    }
    
    if (alert.severity === 'high' || alert.severity === 'medium') {
      return <ExclamationTriangleIcon className={`${iconClass} text-orange-600`} />;
    }
    
    return <InformationCircleIcon className={`${iconClass} text-blue-600`} />;
  };

  const getTypeLabel = () => {
    const labels: Record<AlertType, string> = {
      [AlertType.INFO]: 'Info',
      [AlertType.WARNING]: 'Warning',
      [AlertType.ERROR]: 'Error',
      [AlertType.SECURITY]: 'Security Alert',
      [AlertType.DEBUGGER_TOUCH]: 'Debugger Detected',
      [AlertType.CHAIN_BREAK]: 'Chain Broken',
      [AlertType.LIE_DETECTED]: 'Lie Detected',
      [AlertType.OVERRIDE_SPOKEN]: 'Override Detected',
      [AlertType.YUVA9V_TRIPPED]: 'YUVA-9V Activated',
      [AlertType.SYSTEM]: 'System',
    };
    return labels[alert.type] || alert.type;
  };

  return (
    <div className={getAlertStyles()}>
      <div className="flex-shrink-0">{getIcon()}</div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-900">
              {alert.title}
              <span className="ml-2 text-xs font-normal text-gray-500">
                {getTypeLabel()}
              </span>
            </p>
            <p className="mt-1 text-sm text-gray-700">{alert.message}</p>
            
            {alert.source && (
              <p className="mt-1 text-xs text-gray-500">
                Source: {alert.source}
              </p>
            )}
            
            {alert.action_url && (
              <a
                href={alert.action_url}
                className="mt-2 inline-block text-xs text-blue-600 hover:text-blue-800 underline"
              >
                View Details →
              </a>
            )}
          </div>
          
          <button
            onClick={handleDismiss}
            className="ml-3 flex-shrink-0 rounded-md p-1 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400"
            aria-label="Dismiss alert"
          >
            <XMarkIcon className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        
        <div className="mt-2 text-xs text-gray-400">
          {new Date(alert.created_at).toLocaleString()}
        </div>
      </div>
    </div>
  );
};

export default AlertNotification;
