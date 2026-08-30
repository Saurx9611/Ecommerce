import { apiClient } from './client';

export interface PaymentChargePayload {
  order_id: number;
  simulate_failure?: boolean;
  simulate_timeout?: boolean;
}

export interface PaymentChargeResponse {
  status: 'PAID' | 'FAILED';
  order_id: number;
  transaction_id?: string;
  total_amount?: number;
  message?: string;
}

export interface PaymentStatusResponse {
  order_id: number;
  status: 'PENDING' | 'PROCESSING' | 'PAID' | 'FAILED' | 'CANCELLED';
  total_amount: number;
  created_at: string;
  updated_at: string;
}

export const paymentsApi = {
  charge: async (payload: PaymentChargePayload, idempotencyKey: string): Promise<PaymentChargeResponse> => {
    return apiClient.post<PaymentChargeResponse>('/payments/charge', payload, {
      headers: {
        'Idempotency-Key': idempotencyKey
      }
    });
  },

  getStatus: async (orderId: number): Promise<PaymentStatusResponse> => {
    return apiClient.get<PaymentStatusResponse>(`/payments/status/${orderId}`);
  }
};
