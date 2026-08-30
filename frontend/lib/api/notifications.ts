import { apiClient } from './client';

export type Notification = {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
};

export const notificationsApi = {
  list: (unreadOnly: boolean = false) => {
    const query = unreadOnly ? '?unread_only=true' : '';
    return apiClient<Notification[]>(`/api/notifications${query}`);
  },
  markAsRead: (id: number) => apiClient<Notification>(`/api/notifications/${id}/read`, { method: 'PATCH' }),
  markAllAsRead: () => apiClient<{ message: string }>('/api/notifications/read-all', { method: 'POST' }),
};
