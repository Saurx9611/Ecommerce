'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Radio, Search, FolderKanban, Layers, Settings, LifeBuoy, LogIn, UserPlus } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const navItems = [
  { name: 'Discover & Ingest', href: '/', icon: Radio },
  { name: 'Episodes & Pipeline', href: '/orders', icon: Layers },
  { name: 'Semantic Search', href: '/wishlist', icon: Search },
  { name: 'Projects & Workspaces', href: '/categories', icon: FolderKanban },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { userId } = useAuth();

  const authNavItems = userId
    ? [{ name: 'Settings', href: '/settings', icon: Settings }]
    : [
        { name: 'Login', href: '/login', icon: LogIn },
        { name: 'Register', href: '/register', icon: UserPlus },
      ];

  const currentNavItems = [...navItems.filter(item => item.name !== 'Settings'), ...authNavItems];

  return (
    <div className="w-64 bg-white border-r border-[#E5E7EB] h-screen flex flex-col flex-shrink-0 hidden md:flex">
      <div className="h-16 flex items-center px-6 border-b border-[#E5E7EB] bg-white mb-2">
        <div className="flex items-center gap-2.5">
           <div className="w-8 h-8 bg-[#0EA5E9] rounded-lg flex items-center justify-center text-white font-bold shadow-sm">
             <Radio className="w-4 h-4" />
           </div>
           <div className="flex flex-col">
             <span className="text-sm font-bold tracking-tight uppercase leading-tight text-[#111827]">Podcast</span>
             <span className="text-[10px] font-semibold text-[#0EA5E9] tracking-wider uppercase -mt-0.5">Explorer AI</span>
           </div>
        </div>
      </div>
      <div className="flex-1 py-6 px-4 space-y-1.5 overflow-y-auto">
        {currentNavItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                isActive
                  ? 'bg-[#F0F9FF] text-[#0EA5E9] font-semibold shadow-xs'
                  : 'text-[#6B7280] hover:bg-gray-50 font-medium'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="text-sm">{item.name}</span>
            </Link>
          );
        })}
      </div>
      <div className="p-4 border-t border-[#E5E7EB] bg-gray-50/50">
         <div className="text-[11px] text-gray-500 font-medium px-2 py-1">
           pgvector 768-dim Engine
         </div>
      </div>
    </div>
  );
}
