'use client';

import { useState, useEffect } from 'react';
import { Sparkles, X, CheckCircle2, Cpu, Network, FileText, Loader2 } from 'lucide-react';
import { episodesApi, EpisodeInsight } from '@/lib/api/episodes';

interface EpisodeInsightsModalProps {
  episodeId: number;
  episodeTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function EpisodeInsightsModal({ episodeId, episodeTitle, isOpen, onClose }: EpisodeInsightsModalProps) {
  const [insight, setInsight] = useState<EpisodeInsight | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'competencies' | 'stack' | 'blueprint' | 'resume'>('overview');

  useEffect(() => {
    if (isOpen && episodeId) {
      setLoading(true);
      setError(null);
      episodesApi.getInsights(episodeId)
        .then((data) => {
          setInsight(data);
          setLoading(false);
        })
        .catch((err) => {
          setError(err.message || 'Insights are still processing or not yet generated.');
          setLoading(false);
        });
    }
  }, [isOpen, episodeId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl border border-[#E5E7EB] shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
        
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-[#E5E7EB] flex items-center justify-between bg-gradient-to-r from-sky-50/50 to-white">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-[#0EA5E9]/10 rounded-xl text-[#0EA5E9]">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#0EA5E9] bg-sky-50 px-2 py-0.5 rounded border border-sky-100">
                  AI Intelligence
                </span>
                <span className="text-xs text-gray-500 font-mono">Episode #{episodeId}</span>
              </div>
              <h2 className="text-xl font-bold text-[#111827] mt-0.5 line-clamp-1">{episodeTitle}</h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Navigation Tabs */}
        <div className="flex border-b border-[#E5E7EB] px-6 gap-2 bg-gray-50/50 overflow-x-auto">
          {[
            { id: 'overview', label: 'Overview', icon: Sparkles },
            { id: 'competencies', label: 'Target Competencies', icon: CheckCircle2 },
            { id: 'stack', label: 'Tech Stack', icon: Cpu },
            { id: 'blueprint', label: 'Architectural Blueprint', icon: Network },
            { id: 'resume', label: 'Resume Impact', icon: FileText },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-3.5 px-3 text-sm font-semibold border-b-2 transition-all whitespace-nowrap ${
                  isActive
                    ? 'border-[#0EA5E9] text-[#0EA5E9]'
                    : 'border-transparent text-[#6B7280] hover:text-[#111827]'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Modal Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <Loader2 className="w-8 h-8 text-[#0EA5E9] animate-spin" />
              <p className="text-sm font-medium text-gray-500">Synthesizing intelligence insights...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 text-amber-800 text-sm">
              <p className="font-semibold">Insights Unavailable</p>
              <p className="mt-1 text-xs">{error}</p>
            </div>
          )}

          {!loading && !error && insight && (
            <div className="space-y-6">
              
              {/* Tab 1: Overview */}
              {activeTab === 'overview' && (
                <div className="space-y-4">
                  <div className="p-5 bg-[#F0F9FF] rounded-xl border border-sky-100 text-sm leading-relaxed text-[#111827]">
                    <h3 className="font-bold text-[#0EA5E9] mb-2 text-base">Executive Technical Summary</h3>
                    <p>{insight.overview}</p>
                  </div>
                </div>
              )}

              {/* Tab 2: Competencies */}
              {activeTab === 'competencies' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {insight.target_competencies.map((comp, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-white border border-[#E5E7EB] shadow-xs hover:border-[#0EA5E9] transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-bold text-sm text-[#111827]">{comp.title}</h4>
                        <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-bold uppercase rounded border border-emerald-200">
                          {comp.level}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 leading-relaxed">{comp.description}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 3: Core Tech Stack */}
              {activeTab === 'stack' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {insight.core_tech_stack.map((cat, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-white border border-[#E5E7EB]">
                      <h4 className="font-bold text-xs uppercase tracking-wider text-gray-500 mb-3">{cat.category}</h4>
                      <div className="flex flex-wrap gap-2">
                        {cat.technologies.map((tech, tIdx) => (
                          <span key={tIdx} className="px-3 py-1 bg-gray-100 hover:bg-[#F0F9FF] hover:text-[#0EA5E9] text-gray-800 text-xs font-medium rounded-lg border border-gray-200 transition-colors">
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 4: Architectural Blueprint */}
              {activeTab === 'blueprint' && (
                <div className="space-y-4">
                  {Object.entries(insight.architectural_blueprint).map(([key, val], idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-gray-50 border border-gray-200">
                      <div className="font-mono text-xs font-bold text-[#0EA5E9] uppercase mb-1">
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div className="text-sm font-medium text-gray-900 bg-white p-3 rounded-lg border border-gray-200 font-mono">
                        {val}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 5: Resume Transformation */}
              {activeTab === 'resume' && (
                <div className="space-y-4">
                  {insight.resume_transformation.map((item, idx) => (
                    <div key={idx} className="p-4 rounded-xl bg-white border border-[#E5E7EB] space-y-2">
                      <div className="flex items-start gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#0EA5E9] mt-2 shrink-0" />
                        <p className="text-sm font-semibold text-[#111827]">{item.bullet}</p>
                      </div>
                      <div className="pl-3.5 text-xs text-emerald-600 font-medium">
                        <span className="font-bold text-gray-500 uppercase text-[10px]">Impact: </span>
                        {item.impact}
                      </div>
                    </div>
                  ))}
                </div>
              )}

            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-[#E5E7EB] bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 text-sm font-semibold rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-800 transition-colors"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}
