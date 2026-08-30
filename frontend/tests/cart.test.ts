import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { CartProvider, useCart } from '../context/CartContext';
import { ordersApi } from '../lib/api/orders';

describe('CartContext & Operations', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    React.createElement(CartProvider, null, children)
  );

  it('should initialize with empty items', () => {
    const { result } = renderHook(() => useCart(), { wrapper });
    expect(result.current.items).toEqual([]);
    expect(result.current.totalItems).toBe(0);
    expect(result.current.totalAmount).toBe(0);
  });

  it('should add products respecting stock limits', () => {
    const { result } = renderHook(() => useCart(), { wrapper });

    act(() => {
      result.current.addItem({ id: 1, title: 'RTX 4090 GPU', price: 1599.99, stock: 5 }, 2);
    });

    expect(result.current.items.length).toBe(1);
    expect(result.current.items[0].quantity).toBe(2);
    expect(result.current.totalItems).toBe(2);
    expect(result.current.totalAmount).toBeCloseTo(3199.98);

    // Adding more items up to stock limit
    act(() => {
      result.current.addItem({ id: 1, title: 'RTX 4090 GPU', price: 1599.99, stock: 5 }, 10);
    });

    // Capped at max stock = 5
    expect(result.current.items[0].quantity).toBe(5);
    expect(result.current.totalItems).toBe(5);
  });

  it('should update quantities and remove when qty reaches 0', () => {
    const { result } = renderHook(() => useCart(), { wrapper });

    act(() => {
      result.current.addItem({ id: 2, title: 'Mechanical Keyboard', price: 120.00, stock: 10 }, 3);
    });

    act(() => {
      result.current.updateQuantity(2, 5);
    });
    expect(result.current.items[0].quantity).toBe(5);

    act(() => {
      result.current.updateQuantity(2, 0);
    });
    expect(result.current.items.length).toBe(0);
  });

  it('should execute multi-item checkout and clear cart on success', async () => {
    const { result } = renderHook(() => useCart(), { wrapper });

    act(() => {
      result.current.addItem({ id: 1, title: 'Item 1', price: 100, stock: 5 }, 1);
      result.current.addItem({ id: 2, title: 'Item 2', price: 200, stock: 5 }, 2);
    });

    const mockOrder = { order_id: 101, status: 'PAID', total_amount: 500 };
    vi.spyOn(ordersApi, 'flashCheckout').mockResolvedValue(mockOrder);

    let checkoutResult;
    await act(async () => {
      checkoutResult = await result.current.checkout();
    });

    expect(checkoutResult).toEqual(mockOrder);
    expect(result.current.items.length).toBe(0);
  });
});
