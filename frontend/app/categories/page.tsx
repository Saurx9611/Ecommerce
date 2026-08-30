'use client';

import { useState, useEffect } from 'react';
import { FolderKanban, Plus, Layers, Radio, Trash2, Edit2, Check, X, ArrowRight, Package } from 'lucide-react';
import { projectsApi, Project } from '@/lib/api/projects';
import { productsApi, CategoriesSummary } from '@/lib/api/products';
import Link from 'next/link';

export default function ProjectsAndCategoriesPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [catSummary, setCatSummary] = useState<CategoriesSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      const [projList, cats] = await Promise.all([
        projectsApi.list().catch(() => []),
        productsApi.getCategoriesSummary().catch(() => null)
      ]);
      setProjects(projList);
      setCatSummary(cats);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      await projectsApi.create({ name: newProjectName, description: newProjectDesc });
      setNewProjectName('');
      setNewProjectDesc('');
      setShowCreate(false);
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpdate = async (id: number) => {
    if (!editName.trim()) return;
    try {
      await projectsApi.update(id, { name: editName });
      setEditingId(null);
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this project and all its podcast episodes?')) return;
    try {
      await projectsApi.delete(id);
      loadData();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-8">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-[#0EA5E9]" />
            <h1 className="text-2xl font-bold tracking-tight text-[#111827]">Workspaces & Product Categories</h1>
          </div>
          <p className="text-[#6B7280] text-sm mt-1">Organize your podcasts into vector workspaces and view hardware inventory categories.</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2.5 bg-[#0EA5E9] hover:bg-[#0284C7] text-white text-sm font-semibold rounded-xl transition-all shadow-xs flex items-center gap-2 self-start"
        >
          <Plus className="w-4 h-4" />
          Create Project
        </button>
      </div>

      {/* Categories Summary Banner */}
      {catSummary && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 bg-white rounded-2xl border border-[#E5E7EB] shadow-2xs">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Total Active Products</span>
            <div className="text-2xl font-extrabold text-[#111827] mt-1">{catSummary.total_products} Items</div>
          </div>
          <div className="p-4 bg-white rounded-2xl border border-[#E5E7EB] shadow-2xs">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Warehouse Stock</span>
            <div className="text-2xl font-extrabold text-emerald-600 mt-1">{catSummary.total_stock} Units</div>
          </div>
          <div className="p-4 bg-white rounded-2xl border border-[#E5E7EB] shadow-2xs">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">Active Workspaces</span>
            <div className="text-2xl font-extrabold text-[#0EA5E9] mt-1">{projects.length} Projects</div>
          </div>
        </div>
      )}

      {/* Create Dialog */}
      {showCreate && (
        <form onSubmit={handleCreate} className="p-5 bg-white rounded-2xl border border-sky-200 shadow-sm space-y-4 animate-in fade-in duration-150">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-[#111827]">New Intelligence Workspace</h3>
            <button type="button" onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Project Name (e.g., Cloud Architecture Series)"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              className="px-3.5 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:border-[#0EA5E9]"
              required
            />
            <input
              type="text"
              placeholder="Description (Optional)"
              value={newProjectDesc}
              onChange={(e) => setNewProjectDesc(e.target.value)}
              className="px-3.5 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm outline-none focus:border-[#0EA5E9]"
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="submit"
              className="px-4 py-2 bg-[#0EA5E9] hover:bg-[#0284C7] text-white text-xs font-semibold rounded-lg"
            >
              Create Workspace
            </button>
          </div>
        </form>
      )}

      {/* Projects Grid */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-[#111827]">Intelligence Workspaces</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {loading && projects.length === 0 ? (
            <p className="text-sm text-gray-500 col-span-3 py-12 text-center">Loading workspaces...</p>
          ) : projects.length === 0 ? (
            <div className="col-span-3 p-12 text-center bg-white rounded-2xl border border-dashed border-gray-200 space-y-3">
              <FolderKanban className="w-8 h-8 text-gray-400 mx-auto" />
              <h3 className="text-sm font-bold text-gray-900">No projects created yet</h3>
              <p className="text-xs text-gray-500">Create a project workspace to begin organizing your episodes.</p>
            </div>
          ) : (
            projects.map((p) => (
              <div key={p.id} className="p-6 bg-white rounded-2xl border border-[#E5E7EB] hover:shadow-md transition-shadow flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-start justify-between mb-2">
                    {editingId === p.id ? (
                      <div className="flex items-center gap-1.5 w-full mr-2">
                        <input
                          type="text"
                          defaultValue={p.name}
                          onChange={(e) => setEditName(e.target.value)}
                          className="px-2 py-1 bg-white border border-[#0EA5E9] rounded text-sm w-full outline-none"
                          autoFocus
                        />
                        <button onClick={() => handleUpdate(p.id)} className="p-1 bg-[#0EA5E9] text-white rounded">
                          <Check className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ) : (
                      <h3 className="text-lg font-bold text-[#111827]">{p.name}</h3>
                    )}
                    
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={() => {
                          setEditingId(p.id);
                          setEditName(p.name);
                        }}
                        className="p-1 text-gray-400 hover:text-gray-700 rounded"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="p-1 text-gray-400 hover:text-red-500 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">
                    {p.description || 'Workspace container for podcast ingestion, vector search, and insights.'}
                  </p>
                </div>

                <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-700 flex items-center gap-1.5">
                    <Radio className="w-3.5 h-3.5 text-[#0EA5E9]" />
                    {p.episode_count} Episodes
                  </span>
                  
                  <Link
                    href={`/?project_id=${p.id}`}
                    className="text-xs font-bold text-[#0EA5E9] hover:underline flex items-center gap-1"
                  >
                    Explore <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

    </div>
  );
}
