'use client';

import { useState, useEffect } from 'react';
import { Search, Bell, ShoppingBag, Menu, Sparkles, X, User } from 'lucide-react';
import { notificationsApi, Notification } from '@/lib/api/notifications';
import { useAuth } from '@/context/AuthContext';
import { useCart } from '@/context/CartContext';

export function Header() {
  const [unreadNotifications, setUnreadNotifications] = useState<Notification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const { userId, token } = useAuth();
  const { totalItems, setIsCartOpen } = useCart();

  useEffect(() => {
    async function loadNotifications() {
      try {
        const notifs = await notificationsApi.list(true);
        setUnreadNotifications(notifs);
      } catch (err) {
        // Fallback silently if offline
      }
    }
    loadNotifications();
    const interval = setInterval(loadNotifications, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setUnreadNotifications([]);
      setShowNotifications(false);
    } catch (e) {}
  };

  const userInitial = userId ? `U${userId}` : 'PE';

  return (
    <header className="h-16 bg-white border-b border-[#E5E7EB] flex items-center justify-between px-4 sm:px-8 sticky top-0 z-20 flex-shrink-0">
      <div className="flex items-center flex-1">
        <button className="md:hidden p-2 text-gray-400 hover:text-gray-500 mr-2 rounded-md hover:bg-gray-50 transition-colors">
          <Menu className="h-5 w-5" />
        </button>
        <div className="relative w-full max-w-md hidden sm:block">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-[#9CA3AF]" />
          </div>
          <input
            type="text"
            placeholder="Search transcripts, concepts, products..."
            className="block w-full pl-10 pr-3 py-2 border border-[#E5E7EB] rounded-md text-sm bg-gray-50 focus:bg-white focus:ring-1 focus:ring-[#0EA5E9] outline-none transition-all text-[#111827] placeholder-[#9CA3AF]"
          />
        </div>
      </div>
      
      <div className="flex items-center gap-3 sm:gap-5 relative">
        
        {/* Shopping Cart Button with Real Item Count */}
        <button 
          onClick={() => setIsCartOpen(true)}
          className="relative p-2 text-[#6B7280] hover:text-[#0EA5E9] transition-colors rounded-full hover:bg-gray-50 flex items-center"
          title="Shopping Cart"
        >
          <ShoppingBag className="h-5 w-5" />
          {totalItems > 0 && (
            <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#0EA5E9] text-[10px] font-bold text-white border-2 border-white">
              {totalItems}
            </span>
          )}
        </button>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button 
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 text-[#6B7280] hover:text-[#0EA5E9] transition-colors rounded-full hover:bg-gray-50"
            title="Notifications"
          >
            {unreadNotifications.length > 0 && (
              <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#0EA5E9] text-[10px] font-bold text-white border-2 border-white">
                {unreadNotifications.length}
              </span>
            )}
            <Bell className="h-5 w-5" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-[#E5E7EB] rounded-xl shadow-xl z-50 p-4 animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="flex items-center justify-between pb-2 border-b border-[#E5E7EB]">
                <h4 className="text-xs font-bold uppercase tracking-wider text-[#6B7280]">Pipeline Notifications</h4>
                {unreadNotifications.length > 0 && (
                  <button onClick={handleMarkAllRead} className="text-[11px] text-[#0EA5E9] hover:underline font-semibold">
                    Mark read
                  </button>
                )}
              </div>
              <div className="mt-3 space-y-2 max-h-64 overflow-y-auto">
                {unreadNotifications.length === 0 ? (
                  <p className="text-xs text-[#9CA3AF] text-center py-4">No unread notifications</p>
                ) : (
                  unreadNotifications.map((n) => (
                    <div key={n.id} className="p-2.5 rounded-lg bg-[#F0F9FF] text-xs text-[#111827] border border-blue-100">
                      <div className="font-semibold text-[#0EA5E9]">{n.title}</div>
                      <div className="text-[11px] text-gray-600 mt-0.5">{n.message}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className="hidden sm:flex items-center gap-1.5 bg-[#F0F9FF] px-3 py-1 rounded-full border border-sky-100">
          <Sparkles className="w-3.5 h-3.5 text-[#0EA5E9]" />
          <span className="text-xs font-semibold text-[#0EA5E9]">pgvector AI</span>
        </div>

        {/* Dynamic Authenticated User Avatar */}
        <div 
          className="h-8 w-8 rounded-full bg-gradient-to-tr from-[#0EA5E9] to-sky-400 flex items-center justify-center text-white font-bold text-xs shadow-sm cursor-pointer"
          title={userId ? `Logged in as User #${userId}` : 'Guest Session'}
        >
          {userInitial}
        </div>
      </div>
    </header>
  );
}
