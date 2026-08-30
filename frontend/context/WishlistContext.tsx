'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

type WishlistContextType = {
  wishlistIds: number[];
  toggleWishlist: (id: number) => void;
  isInWishlist: (id: number) => boolean;
};

const WishlistContext = createContext<WishlistContextType | undefined>(undefined);

export function WishlistProvider({ children }: { children: React.ReactNode }) {
  const [wishlistIds, setWishlistIds] = useState<number[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Load from local storage on mount
    const stored = localStorage.getItem('equinox_wishlist');
    if (stored) {
      try {
        setWishlistIds(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse wishlist from local storage', e);
      }
    }
    setIsLoaded(true);
  }, []);

  useEffect(() => {
    // Save to local storage whenever it changes (after initial load)
    if (isLoaded) {
      localStorage.setItem('equinox_wishlist', JSON.stringify(wishlistIds));
    }
  }, [wishlistIds, isLoaded]);

  const toggleWishlist = (id: number) => {
    setWishlistIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id);
      } else {
        return [...prev, id];
      }
    });
  };

  const isInWishlist = (id: number) => wishlistIds.includes(id);

  // Prevent hydration mismatch by not rendering until loaded
  // Alternatively, just provide empty data on first render
  if (!isLoaded) return <div className="hidden" />;

  return (
    <WishlistContext.Provider value={{ wishlistIds, toggleWishlist, isInWishlist }}>
      {children}
    </WishlistContext.Provider>
  );
}

export function useWishlist() {
  const context = useContext(WishlistContext);
  if (context === undefined) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
}
