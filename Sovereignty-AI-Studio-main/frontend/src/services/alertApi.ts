import { Alert, AlertStats } from '../types/alert';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:9898/api/v1';

export class AlertAPI {
  private static async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  static async getAlerts(params?: {
    skip?: number;
    limit?: number;
    unread_only?: boolean;
    alert_type?: string;
  }): Promise<Alert[]> {
    const queryParams = new URLSearchParams();
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.unread_only) queryParams.append('unread_only', 'true');
    if (params?.alert_type) queryParams.append('alert_type', params.alert_type);

    const query = queryParams.toString();
    return this.request<Alert[]>(`/alerts${query ? `?${query}` : ''}`);
  }

  static async getAlertStats(): Promise<AlertStats> {
    return this.request<AlertStats>('/alerts/stats');
  }

  static async getAlert(alertId: number): Promise<Alert> {
    return this.request<Alert>(`/alerts/${alertId}`);
  }

  static async markAsRead(alertId: number): Promise<Alert> {
    return this.request<Alert>(`/alerts/${alertId}/read`, {
      method: 'PATCH',
    });
  }

  static async dismissAlert(alertId: number): Promise<Alert> {
    return this.request<Alert>(`/alerts/${alertId}/dismiss`, {
      method: 'PATCH',
    });
  }

  static async markMultipleAsRead(alertIds: number[]): Promise<{ marked_read: number }> {
    return this.request<{ marked_read: number }>('/alerts/mark-read', {
      method: 'POST',
      body: JSON.stringify(alertIds),
    });
  }

  static async createAlert(alert: {
    type: string;
    title: string;
    message: string;
    source?: string;
    severity?: string;
    action_url?: string;
    user_id?: number;
  }): Promise<Alert> {
    return this.request<Alert>('/alerts/', {
      method: 'POST',
      body: JSON.stringify(alert),
    });
  }
}
