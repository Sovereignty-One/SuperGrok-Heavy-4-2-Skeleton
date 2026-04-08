export enum AlertType {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  SECURITY = 'security',
  DEBUGGER_TOUCH = 'debugger_touch',
  CHAIN_BREAK = 'chain_break',
  LIE_DETECTED = 'lie_detected',
  OVERRIDE_SPOKEN = 'override_spoken',
  YUVA9V_TRIPPED = 'yuva9v_tripped',
  SYSTEM = 'system',
}

export interface Alert {
  id: number;
  user_id?: number;
  type: AlertType;
  title: string;
  message: string;
  source?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  action_url?: string;
  metadata?: string;
  is_read: boolean;
  is_dismissed: boolean;
  created_at: string;
  read_at?: string;
  dismissed_at?: string;
}

export interface AlertStats {
  total: number;
  unread: number;
  by_type: Record<string, number>;
  by_severity: Record<string, number>;
}

export interface WebSocketMessage {
  type: 'alert' | 'system_alert' | 'alert_update';
  data: any;
}
