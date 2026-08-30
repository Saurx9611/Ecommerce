import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { StockWebSocketProvider, useProductStock } from '../context/StockWebSocketContext';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  readyState: number = 1; // OPEN
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((err: any) => void) | null = null;
  sentMessages: string[] = [];

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 10);
  }

  send(data: string) {
    this.sentMessages.push(data);
  }

  close() {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose();
  }
}

// @ts-ignore
global.WebSocket = MockWebSocket;

describe('StockWebSocketContext & Multiplexing', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    React.createElement(StockWebSocketProvider, null, children)
  );

  it('should maintain exactly ONE WebSocket connection across multiple product subscribers in the provider', async () => {
    const { result } = renderHook(
      () => {
        const prod1 = useProductStock(10, 5);
        const prod2 = useProductStock(20, 8);
        return { prod1, prod2 };
      },
      { wrapper }
    );

    expect(result.current.prod1.stock).toBe(5);
    expect(result.current.prod2.stock).toBe(8);

    // Exactly 1 WebSocket connection opened for the entire app provider
    expect(MockWebSocket.instances.length).toBe(1);
    const activeSocket = MockWebSocket.instances[0];

    // Simulate incoming multiplexed stock broadcast from backend
    await act(async () => {
      if (activeSocket.onmessage) {
        activeSocket.onmessage({
          data: JSON.stringify({ type: 'STOCK_UPDATE', product_id: 10, stock: 4 })
        });
      }
    });

    expect(result.current.prod1.stock).toBe(4);
    expect(result.current.prod2.stock).toBe(8); // Untouched
  });
});
