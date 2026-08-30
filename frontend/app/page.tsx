'use client';

import { useState, useEffect } from 'react';
import { Radio, Sparkles, Play, Plus, Clock, Search, Volume2, ArrowUpRight, Cpu, ShoppingBag, Zap } from 'lucide-react';
import { episodesApi, Episode } from '@/lib/api/episodes';
import { productsApi, Product } from '@/lib/api/products';
import { searchApi, SearchResultItem } from '@/lib/api/search';
import { EpisodePlayerModal } from '@/components/EpisodePlayerModal';
import { EpisodeInsightsModal } from '@/components/EpisodeInsightsModal';
import { EpisodeUploadModal } from '@/components/EpisodeUploadModal';
import { ProductCard } from '@/components/ProductCard';

export default function DiscoverPage() {
  const [activeTab, setActiveTab] = useState<'PODCASTS' | 'FLASH_SALE'>('PODCASTS');
  
  // Podcast State
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [episodesLoading, setEpisodesLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);
  const [searching, setSearching] = useState(false);

  // Products State (Real Backend Source of Truth)
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(true);

  // Modals state
  const [selectedEpisode, setSelectedEpisode] = useState<Episode | null>(null);
  const [seekTime, setSeekTime] = useState<number | undefined>(undefined);
  const [isPlayerOpen, setIsPlayerOpen] = useState(false);
  const [insightEpisode, setInsightEpisode] = useState<{ id: number; title: string } | null>(null);
  const [isInsightsOpen, setIsInsightsOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const loadData = async () => {
    try {
      const [eps, prods] = await Promise.all([
        episodesApi.list().catch(() => []),
        productsApi.list().catch(() => [])
      ]);
      setEpisodes(eps);
      setProducts(prods);
    } catch (err) {
      console.error('Failed to load catalog data', err);
    } finally {
      setEpisodesLoading(false);
      setProductsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const resp = await searchApi.search({ query: searchQuery, limit: 8 });
      setSearchResults(resp.results);
    } catch (e) {
      console.error('Search failed', e);
    } finally {
      setSearching(false);
    }
  };

  const openPlayer = (episode: Episode, time?: number) => {
    setSelectedEpisode(episode);
    setSeekTime(time);
    setIsPlayerOpen(true);
  };

  const openInsights = (episode: Episode) => {
    setInsightEpisode({ id: episode.id, title: episode.title });
    setIsInsightsOpen(true);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-[10px] font-bold uppercase tracking-wider">Ready • Indexed</span>;
      case 'failed':
        return <span className="px-2.5 py-1 bg-red-50 text-red-700 border border-red-200 rounded-full text-[10px] font-bold uppercase tracking-wider">Failed</span>;
      case 'queued':
      case 'uploaded':
        return <span className="px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-full text-[10px] font-bold uppercase tracking-wider animate-pulse">Queued</span>;
      default:
        return <span className="px-2.5 py-1 bg-sky-50 text-sky-700 border border-sky-200 rounded-full text-[10px] font-bold uppercase tracking-wider animate-pulse">{status.replace('_', ' ')}</span>;
    }
  };

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-8">
      
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-sky-50/70 via-white to-white p-6 rounded-2xl border border-[#E5E7EB] shadow-xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#0EA5E9] bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-[#0EA5E9]" /> AI Intelligence & Flash Sale Engine
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#111827]">Podcast Explorer & Flash Platform</h1>
          <p className="text-gray-500 text-sm mt-1 max-w-xl">
            Transcribe, diarize, and semantic-index audio with pgvector. Purchase high-demand flash sale hardware with zero-overselling guarantees.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsUploadOpen(true)}
            className="px-5 py-2.5 bg-[#0EA5E9] hover:bg-[#0284C7] text-white font-semibold text-sm rounded-xl transition-all shadow-sm flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Upload Episode
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-gray-200 pb-1">
        <button
          onClick={() => setActiveTab('PODCASTS')}
          className={`px-4 py-2 text-sm font-bold rounded-xl transition-all flex items-center gap-2 ${
            activeTab === 'PODCASTS'
              ? 'bg-gray-900 text-white shadow-xs'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <Radio className="w-4 h-4" />
          Podcast Intelligence ({episodes.length})
        </button>

        <button
          onClick={() => setActiveTab('FLASH_SALE')}
          className={`px-4 py-2 text-sm font-bold rounded-xl transition-all flex items-center gap-2 ${
            activeTab === 'FLASH_SALE'
              ? 'bg-[#0EA5E9] text-white shadow-xs'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <Zap className="w-4 h-4 text-amber-300 fill-amber-300" />
          Live Flash Sale Catalog ({products.length})
        </button>
      </div>

      {activeTab === 'PODCASTS' ? (
        <div className="space-y-8">
          {/* Semantic Search Bar */}
          <div className="bg-white rounded-2xl border border-[#E5E7EB] p-5 shadow-xs">
            <form onSubmit={handleSearch} className="flex gap-3">
              <div className="relative flex-1">
                <Search className="w-5 h-5 text-gray-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search concepts across episodes (e.g. 'How does vector indexing work?')..."
                  className="w-full pl-11 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm outline-none focus:border-[#0EA5E9] focus:bg-white transition-all text-gray-900"
                />
              </div>
              <button
                type="submit"
                disabled={searching}
                className="px-6 py-2.5 bg-[#111827] hover:bg-gray-800 text-white text-sm font-semibold rounded-xl transition-all shadow-xs shrink-0"
              >
                {searching ? 'Searching...' : 'Vector Search'}
              </button>
            </form>

            {/* Search Results Drawer */}
            {searchResults.length > 0 && (
              <div className="mt-6 pt-5 border-t border-gray-100 space-y-3 animate-in fade-in duration-200">
                <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-gray-500">
                  <span>pgvector Similarity Results ({searchResults.length})</span>
                  <button onClick={() => setSearchResults([])} className="text-gray-400 hover:text-gray-700">Clear</button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {searchResults.map((res, i) => {
                    const ep = episodes.find((e) => e.id === res.episode_id);
                    return (
                      <div
                        key={i}
                        onClick={() => ep && openPlayer(ep, res.start_time)}
                        className="p-3.5 rounded-xl bg-[#F0F9FF]/60 hover:bg-[#F0F9FF] border border-sky-100 hover:border-[#0EA5E9] transition-all cursor-pointer space-y-2 group"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-[#0EA5E9]">{res.episode_title}</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 bg-sky-100 text-sky-800 rounded font-bold">
                            Score: {(res.score * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-xs text-gray-700 line-clamp-2 leading-relaxed">{res.text}</p>
                        <div className="flex items-center justify-between text-[11px] text-gray-500 font-mono">
                          <span>{res.speaker}</span>
                          <span className="text-[#0EA5E9] font-bold group-hover:underline flex items-center gap-1">
                            Jump to {Math.floor(res.start_time)}s <ArrowUpRight className="w-3 h-3" />
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Episodes Catalog */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold tracking-tight text-[#111827]">Podcast Episodes</h2>
              <span className="text-xs text-gray-500 font-semibold">{episodes.length} Episodes Processed</span>
            </div>

            {episodesLoading && episodes.length === 0 ? (
              <div className="p-12 text-center bg-white rounded-2xl border border-gray-200">
                <p className="text-sm font-medium text-gray-500">Loading podcast catalog...</p>
              </div>
            ) : episodes.length === 0 ? (
              <div className="p-12 text-center bg-white rounded-2xl border border-dashed border-gray-300 space-y-3">
                <Radio className="w-10 h-10 text-[#0EA5E9] mx-auto opacity-50" />
                <h3 className="text-base font-bold text-gray-900">No episodes ingested yet</h3>
                <p className="text-xs text-gray-500 max-w-sm mx-auto">
                  Upload your first podcast audio file to initiate transcription, speaker diarization, and vector indexing.
                </p>
                <button
                  onClick={() => setIsUploadOpen(true)}
                  className="mt-2 px-4 py-2 bg-[#0EA5E9] text-white text-xs font-semibold rounded-lg hover:bg-[#0284C7] transition-all"
                >
                  Upload First Episode
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {episodes.map((ep) => (
                  <div
                    key={ep.id}
                    className="bg-white rounded-2xl border border-[#E5E7EB] hover:shadow-md transition-shadow p-5 flex flex-col justify-between space-y-4 group"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        {getStatusBadge(ep.status)}
                        <span className="text-[11px] font-mono text-gray-400">#{ep.id}</span>
                      </div>

                      <h3 className="text-base font-bold text-[#111827] group-hover:text-[#0EA5E9] transition-colors line-clamp-2 leading-snug">
                        {ep.title}
                      </h3>
                      <p className="text-xs text-gray-500 mt-1.5 line-clamp-2 leading-relaxed">
                        {ep.description || 'AI indexed episode ready for deep-linked audio search.'}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
                      <span className="flex items-center gap-1 font-mono">
                        <Clock className="w-3.5 h-3.5 text-gray-400" />
                        {ep.duration ? `${Math.floor(ep.duration / 60)}m ${Math.floor(ep.duration % 60)}s` : 'Processing'}
                      </span>
                      <span className="font-mono text-[11px]">
                        {(ep.file_size / (1024 * 1024)).toFixed(1)} MB
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 pt-1">
                      <button
                        onClick={() => openPlayer(ep)}
                        className="py-2 px-3 bg-gray-50 hover:bg-[#F0F9FF] text-[#111827] hover:text-[#0EA5E9] font-semibold text-xs rounded-xl border border-gray-200 hover:border-sky-200 transition-all flex items-center justify-center gap-1.5"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                        Transcript
                      </button>

                      <button
                        onClick={() => openInsights(ep)}
                        className="py-2 px-3 bg-[#0EA5E9] hover:bg-[#0284C7] text-white font-semibold text-xs rounded-xl transition-all shadow-xs flex items-center justify-center gap-1.5"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        AI Insights
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Real Flash Sale Catalog */
        <div className="space-y-6 animate-in fade-in duration-150">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-[#111827]">Hardware & Flash Sale Products</h2>
              <p className="text-xs text-gray-500 mt-0.5">Authoritative stock directly synced with PostgreSQL 16 & Redis admission control.</p>
            </div>
            <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              Live Stock Synchronized
            </span>
          </div>

          {productsLoading && products.length === 0 ? (
            <div className="p-16 bg-white rounded-2xl border border-gray-200 text-center text-sm text-gray-500">
              Loading authoritative product catalog...
            </div>
          ) : products.length === 0 ? (
            <div className="p-16 bg-white rounded-2xl border border-dashed border-gray-300 text-center space-y-3">
              <ShoppingBag className="w-12 h-12 text-gray-300 mx-auto" />
              <h3 className="text-base font-bold text-gray-900">No Flash Products Available</h3>
              <p className="text-xs text-gray-500 max-w-sm mx-auto">
                No products are currently active in the database.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((prod) => (
                <ProductCard key={prod.id} product={prod} isFlashSale={true} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      {selectedEpisode && (
        <EpisodePlayerModal
          episode={selectedEpisode}
          initialSeekTime={seekTime}
          isOpen={isPlayerOpen}
          onClose={() => setIsPlayerOpen(false)}
        />
      )}

      {insightEpisode && (
        <EpisodeInsightsModal
          episodeId={insightEpisode.id}
          episodeTitle={insightEpisode.title}
          isOpen={isInsightsOpen}
          onClose={() => setIsInsightsOpen(false)}
        />
      )}

      <EpisodeUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={loadData}
      />

    </div>
  );
}