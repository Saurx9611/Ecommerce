'use client';

import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { User, LogOut, Settings as SettingsIcon, Server, Database, Sparkles, CheckCircle2 } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api/client';

export default function SettingsPage() {
  const { userId, logout } = useAuth();
  const router = useRouter();
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    fetch(`${API_BASE_URL}/healthz`)
      .then((res) => {
        if (res.ok) setHealth('online');
        else setHealth('offline');
      })
      .catch(() => setHealth('offline'));
  }, []);

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-8">
      <div className="flex items-center gap-3">
        <div className="p-2.5 bg-[#0EA5E9]/10 rounded-xl text-[#0EA5E9]">
          <SettingsIcon className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#111827]">Engine & Platform Settings</h1>
          <p className="text-[#6B7280] text-sm mt-0.5">Manage your environment, vector models, and connection configuration.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl">
        
        {/* Backend Connectivity */}
        <div className="bg-white rounded-2xl p-6 border border-[#E5E7EB] shadow-xs space-y-4">
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <Server className="w-4 h-4 text-[#0EA5E9]" />
            Backend API Health
          </h2>
          
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span className="font-semibold text-gray-700">API Status:</span>
              <span className={`px-2 py-0.5 rounded-full font-bold uppercase text-[10px] ${
                health === 'online' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700'
              }`}>
                {health === 'online' ? 'Connected • 200 OK' : 'Checking / Standby'}
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span className="font-semibold text-gray-700">Base URL:</span>
              <span className="font-mono text-gray-600">{API_BASE_URL}</span>
            </div>
          </div>
        </div>

        {/* Vector Engine Config */}
        <div className="bg-white rounded-2xl p-6 border border-[#E5E7EB] shadow-xs space-y-4">
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <Database className="w-4 h-4 text-[#0EA5E9]" />
            pgvector Index Config
          </h2>
          
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span className="font-semibold text-gray-700">Vector Dimensions:</span>
              <span className="font-mono font-bold text-[#0EA5E9]">768-dim (Cosine)</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-200">
              <span className="font-semibold text-gray-700">Chunking Strategy:</span>
              <span className="font-medium text-gray-700">Speaker-Aware Temporal</span>
            </div>
          </div>
        </div>

        {/* Account Details */}
        <div className="bg-white rounded-2xl p-6 border border-[#E5E7EB] shadow-xs space-y-4 md:col-span-2">
          <h2 className="text-base font-bold text-gray-900 flex items-center gap-2">
            <User className="w-4 h-4 text-gray-500" />
            Account Information
          </h2>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3.5 bg-gray-50 rounded-xl border border-gray-200 text-xs">
              <span className="font-semibold text-gray-700">Active User ID:</span>
              <span className="font-mono font-bold text-gray-900">{userId ? `#${userId}` : 'Demo / Guest User'}</span>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 border border-red-200 text-xs font-semibold rounded-xl text-red-700 bg-white hover:bg-red-50 transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
                Sign Out
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
