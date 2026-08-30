import { apiClient } from './client';

export type SearchResultItem = {
  episode_id: number;
  episode_title: string;
  project_id: number;
  speaker: string;
  text: string;
  start_time: number;
  end_time: number;
  score: number;
};

export type SearchResponse = {
  query: string;
  total_results: number;
  results: SearchResultItem[];
};

export type SavedSearch = {
  id: number;
  user_id: number;
  project_id?: number;
  name: string;
  query: string;
  filters?: Record<string, any>;
  created_at: string;
  updated_at: string;
};

export const searchApi = {
  search: (params: {
    query: string;
    project_id?: number;
    episode_id?: number;
    limit?: number;
    min_score?: number;
  }) => {
    return apiClient<SearchResponse>('/api/search', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  listSaved: (projectId?: number) => {
    const query = projectId ? `?project_id=${projectId}` : '';
    return apiClient<SavedSearch[]>(`/api/search/saved${query}`);
  },

  getSaved: (id: number) => apiClient<SavedSearch>(`/api/search/saved/${id}`),

  createSaved: (data: { name: string; query: string; project_id?: number; filters?: Record<string, any> }) => {
    return apiClient<SavedSearch>('/api/search/saved', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateSaved: (id: number, data: { name?: string; query?: string; filters?: Record<string, any> }) => {
    return apiClient<SavedSearch>(`/api/search/saved/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  deleteSaved: (id: number) => apiClient<void>(`/api/search/saved/${id}`, { method: 'DELETE' }),

  duplicateSaved: (id: number) => {
    return apiClient<SavedSearch>(`/api/search/saved/${id}/duplicate`, {
      method: 'POST',
    });
  },

  runSaved: (id: number) => {
    return apiClient<SearchResponse>(`/api/search/saved/${id}/run`, {
      method: 'POST',
    });
  },
};
