'use client';

import Image from 'next/image';
import { Heart, ShoppingBag } from 'lucide-react';
import { useWishlist } from '@/context/WishlistContext';
import { useCart } from '@/context/CartContext';
import { LiveStockBadge } from '@/components/LiveStockBadge';
import { CheckoutButton } from '@/components/CheckoutButton';

export type Product = {
  id: number;
  title: string;
  description: string | null;
  price: number;
  stock: number;
  category?: string;
  image?: string;
};

type ProductCardProps = {
  product: Product;
  isFlashSale?: boolean;
};

export function ProductCard({ product, isFlashSale = false }: ProductCardProps) {
  const { isInWishlist, toggleWishlist } = useWishlist();
  const { addItem, setIsCartOpen } = useCart();
  const liked = isInWishlist(product.id);

  const priceDisplay = `$${product.price.toFixed(2)}`;

  const handleAddToCart = () => {
    addItem({
      id: product.id,
      title: product.title,
      price: product.price,
      stock: product.stock
    });
    setIsCartOpen(true);
  };

  return (
    <div className="group bg-white rounded-2xl border border-[#E5E7EB] shadow-xs hover:shadow-md transition-shadow overflow-hidden flex flex-col relative">
      <button 
        onClick={() => toggleWishlist(product.id)}
        className="absolute top-3 right-3 z-10 p-2 bg-white/80 backdrop-blur-xs rounded-full hover:bg-white transition-colors border border-gray-100 shadow-2xs"
        title="Add to Wishlist"
      >
        <Heart className={`w-4 h-4 ${liked ? 'fill-rose-500 text-rose-500' : 'text-gray-400'}`} />
      </button>

      <div className="relative h-44 bg-[#F3F4F6] border-b border-[#E5E7EB] overflow-hidden flex items-center justify-center">
        <Image
          src={product.image || `https://picsum.photos/seed/${product.id}/400/400`}
          alt={product.title}
          fill
          className="object-cover transition-transform duration-500 group-hover:scale-105"
          referrerPolicy="no-referrer"
        />
        <div className="absolute top-3 left-3">
          {isFlashSale ? (
            <LiveStockBadge productId={product.id} initialStock={product.stock} />
          ) : (
            product.stock <= 0 ? (
              <span className="px-2 py-1 bg-[#EF4444] rounded text-[10px] font-bold uppercase tracking-wide text-white">Out of Stock</span>
            ) : (
              <span className="px-2 py-1 bg-white/90 backdrop-blur-xs rounded text-[10px] font-bold uppercase tracking-wide text-[#374151] border border-gray-200">
                {product.stock} In Stock
              </span>
            )
          )}
        </div>
      </div>
      
      <div className="p-5 flex flex-col flex-1">
        <div className="flex justify-between items-start mb-2 gap-2">
          <h3 className="font-bold text-base leading-snug group-hover:text-[#0EA5E9] transition-colors line-clamp-2 text-[#111827]">
            {product.title}
          </h3>
          <span className="font-bold text-base shrink-0 text-emerald-600 font-mono">{priceDisplay}</span>
        </div>
        <p className="text-xs text-[#6B7280] mb-4 line-clamp-2 leading-relaxed">
          {product.description || 'High-performance computing and enterprise hardware.'}
        </p>

        <div className="mt-auto space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={handleAddToCart}
              disabled={product.stock <= 0}
              className="py-2 px-3 bg-gray-50 hover:bg-[#F0F9FF] text-[#111827] hover:text-[#0EA5E9] font-semibold text-xs rounded-xl border border-gray-200 hover:border-sky-200 transition-all flex items-center justify-center gap-1.5 disabled:opacity-40"
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              Add to Cart
            </button>
            <CheckoutButton productId={product.id} stock={product.stock} price={product.price} />
          </div>
        </div>
      </div>
    </div>
  );
}
