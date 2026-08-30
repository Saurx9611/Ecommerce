'use client';

import { useState, useEffect } from 'react';
import { Search, Bookmark, Play, Plus, Trash2, Copy, ArrowUpRight, Sparkles, Filter, Loader2 } from 'lucide-react';
import { searchApi, SearchResultItem, SavedSearch } from '@/lib/api/search';
import { episodesApi, Episode } from '@/lib/api/episodes';
import { EpisodePlayerModal } from '@/components/EpisodePlayerModal';

export default function SemanticSearchPage() {
  const [query, setQuery] = useState('');
  const [minScore, setMinScore] = useState(0.0);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [searching, setSearching] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  // Player state
  const [selectedEpisode, setSelectedEpisode] = useState<Episode | null>(null);
  const [seekTime, setSeekTime] = useState<number | undefined>(undefined);
  const [isPlayerOpen, setIsPlayerOpen] = useState(false);

  const loadInitialData = async () => {
    try {
      const [saved, eps] = await Promise.all([
        searchApi.listSaved(),
        episodesApi.list()
      ]);
      setSavedSearches(saved);
      setEpisodes(eps);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    try {
      const res = await searchApi.search({
        query,
        min_score: minScore,
        limit: 20
      });
      setResults(res.results);
    } catch (err) {
      console.error('Search failed', err);
    } finally {
      setSearching(false);
    }
  };

  const handleSaveSearch = async () => {
    if (!query.trim()) return;
    const name = saveName.trim() || query;
    try {
      await searchApi.createSaved({
        name,
        query,
        filters: { min_score: minScore }
      });
      setShowSaveDialog(false);
      setSaveName('');
      const updated = await searchApi.listSaved();
      setSavedSearches(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunSaved = async (savedId: number) => {
    setSearching(true);
    try {
      const res = await searchApi.runSaved(savedId);
      setQuery(res.query);
      setResults(res.results);
    } catch (e) {
      console.error(e);
    } finally {
      setSearching(false);
    }
  };

  const handleDuplicateSaved = async (savedId: number) => {
    try {
      await searchApi.duplicateSaved(savedId);
      const updated = await searchApi.listSaved();
      setSavedSearches(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteSaved = async (savedId: number) => {
    try {
      await searchApi.deleteSaved(savedId);
      setSavedSearches(prev => prev.filter(s => s.id !== savedId));
    } catch (e) {
      console.error(e);
    }
  };

  const openPlayer = (episodeId: number, startSec: number) => {
    const ep = episodes.find(e => e.id === episodeId);
    if (ep) {
      setSelectedEpisode(ep);
      setSeekTime(startSec);
      setIsPlayerOpen(true);
    }
  };

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-8">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Search className="w-5 h-5 text-[#0EA5E9]" />
            <h1 className="text-2xl font-bold tracking-tight text-[#111827]">pgvector Semantic Intelligence</h1>
          </div>
          <p className="text-[#6B7280] text-sm mt-1">
            Query across all podcast transcripts using 768-dimensional normalized vector embeddings and cosine similarity.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left 2 Cols: Search Engine & Deep-Linked Results */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="bg-white p-5 rounded-2xl border border-[#E5E7EB] shadow-xs space-y-4">
            <form onSubmit={handleSearch} className="flex gap-3">
              <div className="relative flex-1">
                <Search className="w-5 h-5 text-gray-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter semantic query (e.g. 'How do you structure microservices?')..."
                  className="w-full pl-11 pr-4 py-2.5 bg-gray-50 border border-[#E5E7EB] rounded-xl text-sm outline-none focus:border-[#0EA5E9] focus:bg-white transition-all text-[#111827]"
                />
              </div>
              <button
                type="submit"
                disabled={searching}
                className="px-6 py-2.5 bg-[#0EA5E9] hover:bg-[#0284C7] text-white text-sm font-semibold rounded-xl transition-all shadow-xs shrink-0 flex items-center gap-2"
              >
                {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                Vector Search
              </button>
            </form>

            <div className="flex items-center justify-between pt-2 border-t border-gray-100 text-xs text-gray-500">
              <div className="flex items-center gap-4">
                <span className="font-semibold text-gray-700">Cosine Distance Threshold:</span>
                <input
                  type="range"
                  min="0"
                  max="0.9"
                  step="0.05"
                  value={minScore}
                  onChange={(e) => setMinScore(parseFloat(e.target.value))}
                  className="w-32 h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#0EA5E9]"
                />
                <span className="font-mono font-bold text-[#0EA5E9]">{(minScore * 100).toFixed(0)}%</span>
              </div>
              {query && (
                <button
                  onClick={() => setShowSaveDialog(!showSaveDialog)}
                  className="text-[#0EA5E9] font-bold hover:underline flex items-center gap-1"
                >
                  <Bookmark className="w-3.5 h-3.5" />
                  Save Search
                </button>
              )}
            </div>

            {showSaveDialog && (
              <div className="p-3 bg-[#F0F9FF] rounded-xl border border-sky-100 flex items-center gap-2 animate-in fade-in duration-150">
                <input
                  type="text"
                  placeholder="Saved Search Name (e.g., Vector Indexing Strategy)"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  className="flex-1 px-3 py-1.5 bg-white border border-sky-200 rounded-lg text-xs outline-none"
                />
                <button
                  onClick={handleSaveSearch}
                  className="px-3 py-1.5 bg-[#0EA5E9] text-white text-xs font-semibold rounded-lg hover:bg-[#0284C7]"
                >
                  Confirm Save
                </button>
              </div>
            )}
          </div>

          {/* Results List */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-[#111827]">
                Ranked Search Results {results.length > 0 && `(${results.length})`}
              </h2>
            </div>

            {searching ? (
              <div className="p-12 bg-white rounded-2xl border border-gray-200 text-center text-sm text-gray-500 flex items-center justify-center gap-2">
                <Loader2 className="w-5 h-5 text-[#0EA5E9] animate-spin" />
                Computing embedding vectors and running similarity ranking...
              </div>
            ) : results.length === 0 ? (
              <div className="p-12 bg-white rounded-2xl border border-dashed border-gray-200 text-center text-sm text-gray-400">
                Type a query above or click a saved search on the right to view deep-linked transcript results.
              </div>
            ) : (
              results.map((res, i) => (
                <div
                  key={i}
                  onClick={() => openPlayer(res.episode_id, res.start_time)}
                  className="p-5 bg-white hover:bg-[#F0F9FF]/40 rounded-2xl border border-[#E5E7EB] hover:border-[#0EA5E9] shadow-xs hover:shadow-md transition-all cursor-pointer space-y-3 group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-[#0EA5E9] bg-sky-50 px-2 py-0.5 rounded border border-sky-100">
                        {res.episode_title}
                      </span>
                      <span className="text-xs font-semibold text-gray-600">{res.speaker}</span>
                    </div>
                    <span className="text-xs font-mono font-bold text-emerald-600 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      Similarity: {(res.score * 100).toFixed(1)}%
                    </span>
                  </div>

                  <p className="text-sm text-gray-800 leading-relaxed">{res.text}</p>

                  <div className="flex items-center justify-between pt-2 border-t border-gray-100 text-xs font-mono text-gray-500">
                    <span>
                      Timestamp: {Math.floor(res.start_time / 60)}m {Math.floor(res.start_time % 60)}s - {Math.floor(res.end_time / 60)}m {Math.floor(res.end_time % 60)}s
                    </span>
                    <span className="text-[#0EA5E9] font-bold group-hover:underline flex items-center gap-1">
                      Seek & Play <Play className="w-3 h-3 fill-current" />
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>

        </div>

        {/* Right 1 Col: Saved Searches Shelf */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-[#111827] flex items-center gap-2">
              <Bookmark className="w-4 h-4 text-[#0EA5E9]" />
              Saved Searches ({savedSearches.length})
            </h3>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-[#E5E7EB] shadow-xs space-y-3">
            {savedSearches.length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-6">No saved searches yet.</p>
            ) : (
              savedSearches.map((s) => (
                <div key={s.id} className="p-3.5 rounded-xl bg-gray-50 hover:bg-[#F0F9FF] border border-gray-200 transition-colors space-y-2">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-[#111827] line-clamp-1">{s.name}</h4>
                      <p className="text-[11px] text-gray-500 font-mono italic mt-0.5 line-clamp-1">"{s.query}"</p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0 ml-2">
                      <button
                        onClick={() => handleDuplicateSaved(s.id)}
                        className="p-1 text-gray-400 hover:text-gray-700 rounded"
                        title="Duplicate Saved Search"
                      >
                        <Copy className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteSaved(s.id)}
                        className="p-1 text-gray-400 hover:text-red-500 rounded"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <button
                    onClick={() => handleRunSaved(s.id)}
                    className="w-full py-1.5 px-2 bg-white hover:bg-[#0EA5E9] text-[#0EA5E9] hover:text-white border border-[#0EA5E9]/30 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1 shadow-2xs"
                  >
                    Run Search <ArrowUpRight className="w-3 h-3" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

      {/* Deep Link Audio Player Modal */}
      {selectedEpisode && (
        <EpisodePlayerModal
          episode={selectedEpisode}
          initialSeekTime={seekTime}
          isOpen={isPlayerOpen}
          onClose={() => setIsPlayerOpen(false)}
        />
      )}

    </div>
  );
}
