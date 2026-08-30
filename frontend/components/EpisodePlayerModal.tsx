'use client';

import { useState, useEffect, useRef } from 'react';
import { Play, Pause, Volume2, SkipBack, SkipForward, X, User, Edit2, Check, Clock, Sparkles } from 'lucide-react';
import { episodesApi, Episode, TranscriptSegment, Speaker } from '@/lib/api/episodes';
import { API_BASE_URL } from '@/lib/api/client';

interface EpisodePlayerModalProps {
  episode: Episode;
  initialSeekTime?: number;
  isOpen: boolean;
  onClose: () => void;
}

export function EpisodePlayerModal({ episode, initialSeekTime, isOpen, onClose }: EpisodePlayerModalProps) {
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([]);
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [editingSpeakerId, setEditingSpeakerId] = useState<number | null>(null);
  const [newSpeakerName, setNewSpeakerName] = useState('');
  
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const segmentRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});

  useEffect(() => {
    if (isOpen && episode) {
      episodesApi.getTranscript(episode.id).then(setTranscript).catch(console.error);
      episodesApi.getSpeakers(episode.id).then(setSpeakers).catch(console.error);
    }
  }, [isOpen, episode]);

  useEffect(() => {
    if (isOpen && initialSeekTime !== undefined && audioRef.current) {
      seekTo(initialSeekTime);
    }
  }, [isOpen, initialSeekTime]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const seekTo = (seconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = seconds;
      setCurrentTime(seconds);
      if (!isPlaying) {
        audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
      }
    }
  };

  const handleSpeakerRename = async (speakerId: number) => {
    if (!newSpeakerName.trim()) return;
    try {
      const updated = await episodesApi.updateSpeaker(episode.id, speakerId, newSpeakerName);
      setSpeakers((prev) => prev.map((s) => (s.id === speakerId ? updated : s)));
      setEditingSpeakerId(null);
    } catch (e) {
      console.error('Failed to rename speaker', e);
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  if (!isOpen) return null;

  const audioSrc = episode.audio_url.startsWith('http') 
    ? episode.audio_url 
    : `${API_BASE_URL}${episode.audio_url}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl border border-[#E5E7EB] shadow-2xl w-full max-w-5xl h-[92vh] flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-[#E5E7EB] flex items-center justify-between bg-white shrink-0">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#0EA5E9] bg-[#F0F9FF] px-2 py-0.5 rounded border border-sky-100">
              Deep-Linked Audio & Transcript
            </span>
            <h2 className="text-lg font-bold text-[#111827] mt-0.5 line-clamp-1">{episode.title}</h2>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Main Grid: Left Speakers/Details, Right Synchronized Transcript */}
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden min-h-0">
          
          {/* Left Column: Audio Visualizer & Speakers */}
          <div className="w-full md:w-80 border-b md:border-b-0 md:border-r border-[#E5E7EB] p-5 flex flex-col bg-gray-50/50 overflow-y-auto shrink-0">
            
            <div className="p-4 bg-white rounded-xl border border-gray-200 shadow-xs mb-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-[#0EA5E9]" />
                Speakers ({speakers.length})
              </h4>
              <div className="space-y-2.5">
                {speakers.map((spk) => (
                  <div key={spk.id} className="p-2.5 rounded-lg bg-gray-50 border border-gray-200 text-xs">
                    {editingSpeakerId === spk.id ? (
                      <div className="flex items-center gap-1.5">
                        <input
                          type="text"
                          defaultValue={spk.display_name}
                          onChange={(e) => setNewSpeakerName(e.target.value)}
                          className="px-2 py-1 bg-white border border-[#0EA5E9] rounded text-xs w-full outline-none"
                          autoFocus
                        />
                        <button onClick={() => handleSpeakerRename(spk.id)} className="p-1 bg-[#0EA5E9] text-white rounded">
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-bold text-gray-900">{spk.display_name}</div>
                          <div className="text-[10px] text-gray-500 font-mono">{spk.label} • {formatTime(spk.speaking_duration)}</div>
                        </div>
                        <button
                          onClick={() => {
                            setEditingSpeakerId(spk.id);
                            setNewSpeakerName(spk.display_name);
                          }}
                          className="p-1 text-gray-400 hover:text-[#0EA5E9] transition-colors"
                          title="Rename Speaker"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-auto p-3.5 bg-[#F0F9FF] rounded-xl border border-sky-100 text-xs text-sky-800">
              <div className="font-bold mb-1 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-[#0EA5E9]" />
                Temporal Seeking
              </div>
              <p className="text-[11px] leading-relaxed text-sky-700">
                Click any timestamp or speech block in the transcript to jump audio playback to that exact second.
              </p>
            </div>
          </div>

          {/* Right Column: Synchronized Timestamped Transcript */}
          <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-white">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-2">Timestamped Transcript</h3>
            {transcript.length === 0 ? (
              <p className="text-sm text-gray-400 py-10 text-center">No transcript available for this episode.</p>
            ) : (
              transcript.map((segment) => {
                const isActive = currentTime >= segment.start_time && currentTime <= segment.end_time;
                return (
                  <div
                    key={segment.id}
                    onClick={() => seekTo(segment.start_time)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer ${
                      isActive
                        ? 'bg-[#F0F9FF] border-[#0EA5E9] shadow-sm'
                        : 'bg-white border-[#E5E7EB] hover:bg-gray-50/80 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-bold text-[#0EA5E9] bg-sky-50 px-2 py-0.5 rounded border border-sky-100">
                        {segment.speaker?.display_name || segment.speaker?.label || 'Speaker'}
                      </span>
                      <span className="text-xs font-mono font-semibold text-gray-500 hover:text-[#0EA5E9] transition-colors">
                        {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed text-[#111827]">{segment.text}</p>
                  </div>
                );
              })
            )}
          </div>

        </div>

        {/* Bottom Audio Controller Bar */}
        <div className="p-4 bg-white border-t border-[#E5E7EB] shrink-0 flex flex-col gap-2">
          <audio
            ref={audioRef}
            src={audioSrc}
            onTimeUpdate={() => audioRef.current && setCurrentTime(audioRef.current.currentTime)}
            onLoadedMetadata={() => audioRef.current && setDuration(audioRef.current.duration)}
            onEnded={() => setIsPlaying(false)}
          />

          {/* Timeline slider */}
          <div className="flex items-center gap-3 w-full">
            <span className="text-xs font-mono text-gray-500 w-10 text-right">{formatTime(currentTime)}</span>
            <input
              type="range"
              min={0}
              max={duration || 100}
              value={currentTime}
              onChange={(e) => seekTo(parseFloat(e.target.value))}
              className="flex-1 h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0EA5E9]"
            />
            <span className="text-xs font-mono text-gray-500 w-10">{formatTime(duration)}</span>
          </div>

          {/* Playback controls */}
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => seekTo(Math.max(0, currentTime - 10))}
              className="p-2 text-gray-600 hover:text-[#0EA5E9] transition-colors"
              title="Back 10s"
            >
              <SkipBack className="w-5 h-5" />
            </button>
            <button
              onClick={togglePlay}
              className="w-11 h-11 rounded-full bg-[#0EA5E9] text-white flex items-center justify-center hover:bg-[#0284C7] transition-all shadow-md"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
            </button>
            <button
              onClick={() => seekTo(Math.min(duration, currentTime + 10))}
              className="p-2 text-gray-600 hover:text-[#0EA5E9] transition-colors"
              title="Forward 10s"
            >
              <SkipForward className="w-5 h-5" />
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
