import { apiClient } from './client';

export interface OrderItemData {
  id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
}

export interface OrderData {
  id: number;
  user_id: number;
  total_amount: number;
  status: 'PENDING' | 'PROCESSING' | 'PAID' | 'FAILED' | 'CANCELLED';
  created_at: string;
  updated_at: string;
  items: OrderItemData[];
}

export interface CreateOrderPayload {
  items: { product_id: number; quantity: number }[];
}

export const ordersApi = {
  list: async (): Promise<OrderData[]> => {
    return apiClient.get<OrderData[]>('/orders/');
  },

  get: async (id: number): Promise<OrderData> => {
    return apiClient.get<OrderData>(`/orders/${id}`);
  },

  flashCheckout: async (payload: CreateOrderPayload, idempotencyKey: string): Promise<any> => {
    return apiClient.post('/orders/flash-checkout', payload, {
      headers: {
        'Idempotency-Key': idempotencyKey
      }
    });
  }
};
