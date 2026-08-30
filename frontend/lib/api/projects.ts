import { apiClient } from './client';

export type Project = {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  episode_count: number;
};

export const projectsApi = {
  list: () => apiClient<Project[]>('/api/projects'),
  get: (id: number) => apiClient<Project>(`/api/projects/${id}`),
  create: (data: { name: string; description?: string }) => {
    return apiClient<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  update: (id: number, data: { name?: string; description?: string }) => {
    return apiClient<Project>(`/api/projects/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
  delete: (id: number) => apiClient<void>(`/api/projects/${id}`, { method: 'DELETE' }),
};
