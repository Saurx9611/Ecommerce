'use client';

import { useState, useEffect } from 'react';
import { Upload, X, Mic, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { episodesApi } from '@/lib/api/episodes';
import { projectsApi, Project } from '@/lib/api/projects';

interface EpisodeUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function EpisodeUploadModal({ isOpen, onClose, onSuccess }: EpisodeUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [projectId, setProjectId] = useState<number | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      projectsApi.list().then((list) => {
        setProjects(list);
        if (list.length > 0) {
          setProjectId(list[0].id);
        }
      }).catch(console.error);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select an audio file (MP3, WAV, M4A).');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title || file.name.replace(/\.[^/.]+$/, ''));
    formData.append('description', description);
    formData.append('project_id', String(projectId || 1));
    formData.append('language', 'en');

    try {
      await episodesApi.upload(formData);
      setLoading(false);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'Upload failed. Please check file format.');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl border border-[#E5E7EB] shadow-2xl w-full max-w-lg overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-5 border-b border-[#E5E7EB] flex items-center justify-between bg-white">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-[#0EA5E9]/10 rounded-lg text-[#0EA5E9]">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#111827]">Ingest Podcast Episode</h2>
              <p className="text-xs text-gray-500">Audio will be transcribed and indexed into pgvector</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3.5 bg-red-50 rounded-xl border border-red-200 text-red-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* File dropzone */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-2">Audio File</label>
            <div className="border-2 border-dashed border-gray-200 hover:border-[#0EA5E9] rounded-xl p-6 text-center bg-gray-50/50 transition-colors cursor-pointer relative">
              <input
                type="file"
                accept="audio/*"
                onChange={(e) => {
                  const selected = e.target.files?.[0] || null;
                  setFile(selected);
                  if (selected && !title) {
                    setTitle(selected.name.replace(/\.[^/.]+$/, ''));
                  }
                }}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                required
              />
              <Mic className="w-8 h-8 text-[#0EA5E9] mx-auto mb-2" />
              {file ? (
                <div className="text-xs font-semibold text-gray-900">
                  {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                </div>
              ) : (
                <>
                  <p className="text-xs font-semibold text-gray-700">Click or drag & drop audio here</p>
                  <p className="text-[11px] text-gray-400 mt-1">Supports MP3, WAV, M4A, OGG up to 150MB</p>
                </>
              )}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">Episode Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Distributed Consensus in Cloud Systems"
              className="w-full px-3.5 py-2.5 bg-gray-50 border border-[#E5E7EB] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:bg-white transition-all text-[#111827]"
              required
            />
          </div>

          {/* Project selector */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">Workspace / Project</label>
            <select
              value={projectId || ''}
              onChange={(e) => setProjectId(Number(e.target.value))}
              className="w-full px-3.5 py-2.5 bg-gray-50 border border-[#E5E7EB] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:bg-white transition-all text-[#111827]"
            >
              {projects.length === 0 && <option value="1">Default Podcast Project</option>}
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-600 mb-1.5">Description (Optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Key topics, guest notes..."
              className="w-full px-3.5 py-2 bg-gray-50 border border-[#E5E7EB] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:bg-white transition-all text-[#111827]"
            />
          </div>

          {/* Buttons */}
          <div className="pt-3 flex justify-end gap-2 border-t border-[#E5E7EB]">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-semibold rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 text-sm font-semibold rounded-lg bg-[#0EA5E9] hover:bg-[#0284C7] text-white transition-all disabled:opacity-50 flex items-center gap-2 shadow-sm"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading & Queuing...
                </>
              ) : (
                'Start Processing'
              )}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}
