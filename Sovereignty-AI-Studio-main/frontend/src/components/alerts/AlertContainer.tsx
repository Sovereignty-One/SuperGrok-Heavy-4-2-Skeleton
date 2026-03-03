import React from 'react';
import { Alert } from '../../types/alert';
import AlertNotification from './AlertNotification';

interface AlertContainerProps {
  alerts: Alert[];
  onDismiss: (id: number) => void;
  onRead: (id: number) => void;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

const AlertContainer: React.FC<AlertContainerProps> = ({
  alerts,
  onDismiss,
  onRead,
  position = 'top-right',
}) => {
  const positionClasses = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
  };

  return (
    <div
      className={`fixed ${positionClasses[position]} z-50 max-w-md w-full pointer-events-none`}
      style={{ maxHeight: '90vh', overflowY: 'auto' }}
    >
      <div className="pointer-events-auto">
        {alerts.map(alert => (
          <AlertNotification
            key={alert.id}
            alert={alert}
            onDismiss={onDismiss}
            onRead={onRead}
          />
        ))}
      </div>
    </div>
  );
};

export default AlertContainer;
