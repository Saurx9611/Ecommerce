import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { WishlistProvider, useWishlist } from '../context/WishlistContext';

describe('WishlistContext', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    React.createElement(WishlistProvider, null, children)
  );

  it('should toggle items in and out of wishlist', () => {
    const { result } = renderHook(() => useWishlist(), { wrapper });

    expect(result.current.isInWishlist(42)).toBe(false);

    act(() => {
      result.current.toggleWishlist(42);
    });
    expect(result.current.isInWishlist(42)).toBe(true);

    act(() => {
      result.current.toggleWishlist(42);
    });
    expect(result.current.isInWishlist(42)).toBe(false);
  });

  it('should persist wishlist to localStorage', () => {
    const { result } = renderHook(() => useWishlist(), { wrapper });

    act(() => {
      result.current.toggleWishlist(10);
      result.current.toggleWishlist(20);
    });

    const stored = JSON.parse(localStorage.getItem('equinox_wishlist') || '[]');
    expect(stored).toEqual([10, 20]);
  });
});
