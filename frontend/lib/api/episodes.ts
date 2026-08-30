import { apiClient } from './client';

export type Speaker = {
  id: number;
  episode_id: number;
  label: string;
  display_name: string;
  speaking_duration: number;
  segment_count: number;
};

export type TranscriptSegment = {
  id: number;
  episode_id: number;
  speaker_id?: number;
  speaker?: Speaker;
  text: string;
  start_time: number;
  end_time: number;
  sequence_number: number;
  confidence: number;
};

export type ProcessingJob = {
  id: number;
  episode_id: number;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  current_stage: 'upload' | 'transcribing' | 'speaker_detection' | 'chunking' | 'embedding' | 'indexing' | 'complete';
  progress: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
};

export type EpisodeInsight = {
  id: number;
  episode_id: number;
  overview: string;
  target_competencies: Array<{
    title: string;
    level: string;
    description: string;
  }>;
  core_tech_stack: Array<{
    category: string;
    technologies: string[];
  }>;
  architectural_blueprint: {
    ingestion_flow: string;
    retrieval_pipeline: string;
    playback_deep_link: string;
  };
  resume_transformation: Array<{
    bullet: string;
    impact: string;
  }>;
  created_at: string;
};

export type Episode = {
  id: number;
  project_id: number;
  title: string;
  description?: string;
  original_filename: string;
  audio_url: string;
  file_size: number;
  mime_type: string;
  duration?: number;
  language?: string;
  status: 'uploaded' | 'queued' | 'transcribing' | 'speaker_detection' | 'chunking' | 'embedding' | 'indexing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  processed_at?: string;
  speakers?: Speaker[];
};

export const episodesApi = {
  list: (projectId?: number) => {
    const query = projectId ? `?project_id=${projectId}` : '';
    return apiClient<Episode[]>(`/api/episodes${query}`);
  },

  get: (id: number) => apiClient<Episode>(`/api/episodes/${id}`),

  upload: (formData: FormData) => {
    return apiClient<Episode>('/api/episodes', {
      method: 'POST',
      body: formData,
    });
  },

  delete: (id: number) => apiClient<void>(`/api/episodes/${id}`, { method: 'DELETE' }),

  getTranscript: (id: number) => apiClient<TranscriptSegment[]>(`/api/episodes/${id}/transcript`),

  getSpeakers: (id: number) => apiClient<Speaker[]>(`/api/episodes/${id}/speakers`),

  updateSpeaker: (episodeId: number, speakerId: number, displayName: string) => {
    return apiClient<Speaker>(`/api/episodes/${episodeId}/speakers/${speakerId}`, {
      method: 'PATCH',
      body: JSON.stringify({ display_name: displayName }),
    });
  },

  getProcessing: (id: number) => apiClient<ProcessingJob>(`/api/episodes/${id}/processing`),

  process: (id: number) => apiClient<ProcessingJob>(`/api/episodes/${id}/process`, { method: 'POST' }),

  getInsights: (id: number) => apiClient<EpisodeInsight>(`/api/episodes/${id}/insights`),
};
