'use client';

import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';

type ConnectionStatus = 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED';

interface StockWebSocketContextType {
  stockMap: Record<number, number>;
  subscribeProduct: (productId: number) => void;
  unsubscribeProduct: (productId: number) => void;
  connectionStatus: ConnectionStatus;
}

const StockWebSocketContext = createContext<StockWebSocketContextType | undefined>(undefined);

export function StockWebSocketProvider({ children }: { children: React.ReactNode }) {
  const [stockMap, setStockMap] = useState<Record<number, number>>({});
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('CLOSED');

  const wsRef = useRef<WebSocket | null>(null);
  const subscribedIdsRef = useRef<Set<number>>(new Set());
  const refCountMapRef = useRef<Map<number, number>>(new Map());
  const reconnectAttemptRef = useRef(0);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const getWsUrl = () => {
    if (process.env.NEXT_PUBLIC_WS_URL) {
      return process.env.NEXT_PUBLIC_WS_URL;
    }
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return apiBase.replace(/^http/, 'ws') + '/api/products/ws/stock';
  };

  const connect = useCallback(() => {
    if (typeof window === 'undefined') return;

    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      setConnectionStatus('CONNECTING');
      const wsUrl = getWsUrl();
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setConnectionStatus('OPEN');
        reconnectAttemptRef.current = 0;

        // Resubscribe to all active product IDs on reconnection
        const activeIds = Array.from(subscribedIdsRef.current);
        if (activeIds.length > 0) {
          socket.send(JSON.stringify({ action: 'subscribe', product_ids: activeIds }));
        }

        // Start heartbeat ping every 25s
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ action: 'ping' }));
          }
        }, 25000);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'STOCK_UPDATE' && typeof data.product_id === 'number' && typeof data.stock === 'number') {
            setStockMap((prev) => ({
              ...prev,
              [data.product_id]: data.stock
            }));
          }
        } catch (err) {
          console.error('Error parsing stock update message:', err);
        }
      };

      socket.onerror = (err) => {
        console.warn('Stock WebSocket encountered error, handling reconnect:', err);
      };

      socket.onclose = () => {
        setConnectionStatus('CLOSED');
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);

        // Exponential backoff reconnect: min(1000 * 2^attempts, 15000) + jitter
        const delay = Math.min(1000 * Math.pow(1.5, reconnectAttemptRef.current), 15000) + Math.random() * 500;
        reconnectAttemptRef.current += 1;

        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      };
    } catch (e) {
      console.warn('Failed to establish WebSocket connection:', e);
      setConnectionStatus('CLOSED');
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const subscribeProduct = useCallback((productId: number) => {
    const currentCount = refCountMapRef.current.get(productId) || 0;
    refCountMapRef.current.set(productId, currentCount + 1);

    if (!subscribedIdsRef.current.has(productId)) {
      subscribedIdsRef.current.add(productId);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'subscribe', product_ids: [productId] }));
      }
    }
  }, []);

  const unsubscribeProduct = useCallback((productId: number) => {
    const currentCount = refCountMapRef.current.get(productId) || 1;
    if (currentCount <= 1) {
      refCountMapRef.current.delete(productId);
      subscribedIdsRef.current.delete(productId);
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'unsubscribe', product_ids: [productId] }));
      }
    } else {
      refCountMapRef.current.set(productId, currentCount - 1);
    }
  }, []);

  return (
    <StockWebSocketContext.Provider
      value={{
        stockMap,
        subscribeProduct,
        unsubscribeProduct,
        connectionStatus
      }}
    >
      {children}
    </StockWebSocketContext.Provider>
  );
}

export function useStockWebSocket() {
  const context = useContext(StockWebSocketContext);
  if (context === undefined) {
    throw new Error('useStockWebSocket must be used within a StockWebSocketProvider');
  }
  return context;
}

export function useProductStock(productId: number, initialStock: number) {
  const { stockMap, subscribeProduct, unsubscribeProduct, connectionStatus } = useStockWebSocket();

  useEffect(() => {
    subscribeProduct(productId);
    return () => {
      unsubscribeProduct(productId);
    };
  }, [productId, subscribeProduct, unsubscribeProduct]);

  const liveStock = stockMap[productId] !== undefined ? stockMap[productId] : initialStock;
  const isLive = connectionStatus === 'OPEN';

  return {
    stock: liveStock,
    isLive,
    connectionStatus
  };
}
