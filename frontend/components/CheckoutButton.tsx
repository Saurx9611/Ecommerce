'use client';
import { useState } from 'react';

interface CheckoutButtonProps {
  productId: number;
  stock: number;
  price: number;
}

export function CheckoutButton({ productId, stock, price }: CheckoutButtonProps) {
  const [stage, setStage] = useState<'IDLE' | 'CREATING_ORDER' | 'PROCESSING_PAYMENT' | 'SUCCESS' | 'FAILED'>('IDLE');
  const [statusMessage, setStatusMessage] = useState('');
  const [orderId, setOrderId] = useState<number | null>(null);

  const handleCheckoutAndPay = async () => {
    setStage('CREATING_ORDER');
    setStatusMessage('Reserving inventory & creating order...');

    const orderIdempotencyKey = `ord-${crypto.randomUUID()}`;
    const paymentIdempotencyKey = `pay-${crypto.randomUUID()}`;

    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

    try {
      // Step 1: Create Order via Flash Checkout
      const orderRes = await fetch(`${apiBase}/orders/flash-checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': orderIdempotencyKey
        },
        body: JSON.stringify({
          items: [{ product_id: productId, quantity: 1 }]
        })
      });

      if (orderRes.status === 410) {
        setStage('FAILED');
        setStatusMessage('Sold Out! Flash sale inventory exhausted.');
        return;
      }

      if (!orderRes.ok) {
        const errorData = await orderRes.json().catch(() => ({ detail: 'Failed to create order' }));
        setStage('FAILED');
        setStatusMessage(`Order error: ${errorData.detail || 'Insufficient inventory'}`);
        return;
      }

      const orderData = await orderRes.json();
      const createdOrderId = orderData.order_id;
      setOrderId(createdOrderId);

      // If order is already settled by flash checkout
      if (orderData.status === 'PAID') {
        setStage('SUCCESS');
        setStatusMessage(`Order #${createdOrderId} Confirmed & Settled!`);
        return;
      }

      // Step 2: Transition into Payment Processing
      setStage('PROCESSING_PAYMENT');
      setStatusMessage(`Charging payment for Order #${createdOrderId}...`);

      const payRes = await fetch(`${apiBase}/payments/charge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': paymentIdempotencyKey
        },
        body: JSON.stringify({
          order_id: createdOrderId
        })
      });

      if (payRes.ok) {
        const payData = await payRes.json();
        setStage('SUCCESS');
        setStatusMessage(`Payment Confirmed! Order #${createdOrderId} (Txn: ${payData.transaction_id || 'Settled'})`);
      } else {
        const payError = await payRes.json().catch(() => ({ detail: 'Payment declined' }));
        setStage('FAILED');
        setStatusMessage(`Payment Failed: ${payError.detail || 'Declined by bank'}. Please retry.`);
      }
    } catch (err) {
      setStage('FAILED');
      setStatusMessage('Network connection error. Please try again.');
    }
  };

  if (stock <= 0) {
    return (
      <button className="w-full py-2.5 text-sm font-semibold rounded-lg bg-gray-200 text-gray-500 cursor-not-allowed" disabled>
        Sold Out
      </button>
    );
  }

  const isLoading = stage === 'CREATING_ORDER' || stage === 'PROCESSING_PAYMENT';

  return (
    <div className="flex flex-col gap-2">
      <button 
        onClick={handleCheckoutAndPay} 
        disabled={isLoading}
        className={`w-full py-2.5 text-sm font-semibold rounded-lg transition-all text-white disabled:opacity-60 ${
          stage === 'SUCCESS' 
            ? 'bg-emerald-600 hover:bg-emerald-700' 
            : stage === 'FAILED'
            ? 'bg-amber-600 hover:bg-amber-700'
            : 'bg-[#0EA5E9] hover:bg-[#0284C7]'
        }`}
      >
        {stage === 'CREATING_ORDER' && 'Reserving Stock...'}
        {stage === 'PROCESSING_PAYMENT' && 'Processing Payment...'}
        {stage === 'SUCCESS' && 'Order Complete!'}
        {stage === 'FAILED' && 'Retry Checkout'}
        {stage === 'IDLE' && `Buy Now • $${price.toFixed(2)}`}
      </button>

      {statusMessage && (
        <p className={`text-xs text-center font-medium ${
          stage === 'SUCCESS' 
            ? 'text-emerald-700 dark:text-emerald-400' 
            : stage === 'FAILED'
            ? 'text-rose-600 dark:text-rose-400'
            : 'text-zinc-600 dark:text-zinc-300'
        }`}>
          {statusMessage}
        </p>
      )}
    </div>
  );
}