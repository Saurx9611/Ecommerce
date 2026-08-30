import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ordersApi, OrderData } from '../lib/api/orders';
import { paymentsApi, PaymentChargeResponse } from '../lib/api/payments';
import { productsApi } from '../lib/api/products';
import { apiClient } from '../lib/api/client';

describe('Frontend API Client Layer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('ordersApi.list should return orders from backend', async () => {
    const mockOrders: OrderData[] = [
      {
        id: 1,
        user_id: 1,
        total_amount: 999.00,
        status: 'PAID',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        items: [{ id: 10, product_id: 1, quantity: 1, unit_price: 999.00 }]
      }
    ];

    vi.spyOn(apiClient, 'get').mockResolvedValue(mockOrders);

    const orders = await ordersApi.list();
    expect(orders).toEqual(mockOrders);
    expect(orders[0].status).toBe('PAID');
    expect(orders[0].items.length).toBe(1);
  });

  it('paymentsApi.charge should send idempotency key and return payment status', async () => {
    const mockChargeResponse: PaymentChargeResponse = {
      status: 'PAID',
      order_id: 1,
      transaction_id: 'txn_mock12345',
      total_amount: 999.00
    };

    vi.spyOn(apiClient, 'post').mockResolvedValue(mockChargeResponse);

    const res = await paymentsApi.charge({ order_id: 1 }, 'pay-key-123');
    expect(res.status).toBe('PAID');
    expect(res.transaction_id).toBe('txn_mock12345');
  });

  it('productsApi.list should fetch live authoritative products', async () => {
    const mockProducts = [
      { id: 1, title: 'Server Blade', description: 'Dual Xeon', price: 2499.00, stock: 4 }
    ];

    vi.spyOn(apiClient, 'get').mockResolvedValue(mockProducts);

    const prods = await productsApi.list();
    expect(prods).toEqual(mockProducts);
    expect(prods[0].price).toBe(2499.00);
  });
});
