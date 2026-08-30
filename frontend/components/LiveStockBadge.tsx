'use client';

import { useProductStock } from '@/context/StockWebSocketContext';
import { Activity } from 'lucide-react';

type LiveStockBadgeProps = {
  productId: number;
  initialStock: number;
};

export function LiveStockBadge({ productId, initialStock }: LiveStockBadgeProps) {
  const { stock, isLive } = useProductStock(productId, initialStock);

  if (stock <= 0) {
    return (
      <span className="px-2.5 py-1 bg-[#EF4444] rounded-lg text-[10px] font-bold uppercase tracking-wide text-white shadow-2xs">
        Sold Out
      </span>
    );
  }

  return (
    <span className={`px-2.5 py-1 backdrop-blur-xs rounded-lg text-[10px] font-bold uppercase tracking-wide border transition-all flex items-center gap-1 shadow-2xs ${
      stock <= 3 
        ? 'bg-amber-50 text-amber-700 border-amber-200 animate-pulse'
        : 'bg-white/95 text-[#111827] border-gray-200'
    }`}>
      {isLive && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping shrink-0" />}
      {stock} {stock === 1 ? 'Unit Left' : 'Units Left'}
    </span>
  );
}
