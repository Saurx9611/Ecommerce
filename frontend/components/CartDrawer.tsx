'use client';

import { useState } from 'react';
import { ShoppingBag, X, Plus, Minus, Trash2, ArrowRight, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { useCart } from '@/context/CartContext';
import { paymentsApi } from '@/lib/api/payments';

export function CartDrawer() {
  const { items, isCartOpen, setIsCartOpen, removeItem, updateQuantity, totalAmount, clearCart, checkout } = useCart();
  const [stage, setStage] = useState<'IDLE' | 'CHECKING_OUT' | 'SETTLING_PAYMENT' | 'SUCCESS' | 'ERROR'>('IDLE');
  const [statusMessage, setStatusMessage] = useState('');
  const [confirmedOrderId, setConfirmedOrderId] = useState<number | null>(null);

  if (!isCartOpen) return null;

  const handleCheckoutAndPay = async () => {
    try {
      setStage('CHECKING_OUT');
      setStatusMessage('Reserving cart inventory...');

      const orderResult = await checkout();
      const orderId = orderResult.order_id;
      setConfirmedOrderId(orderId);

      if (orderResult.status === 'PAID') {
        setStage('SUCCESS');
        setStatusMessage(`Order #${orderId} confirmed and paid successfully!`);
        return;
      }

      setStage('SETTLING_PAYMENT');
      setStatusMessage(`Charging payment for Order #${orderId}...`);

      const paymentKey = `cart-pay-${crypto.randomUUID()}`;
      const payResult = await paymentsApi.charge({ order_id: orderId }, paymentKey);

      if (payResult.status === 'PAID') {
        setStage('SUCCESS');
        setStatusMessage(`Payment settled for Order #${orderId}! (Txn: ${payResult.transaction_id || 'Settled'})`);
      } else {
        setStage('ERROR');
        setStatusMessage('Payment declined by card gateway.');
      }
    } catch (err: any) {
      setStage('ERROR');
      setStatusMessage(err?.message || 'Checkout failed. Please review cart quantities.');
    }
  };

  const handleClose = () => {
    setIsCartOpen(false);
    if (stage === 'SUCCESS') {
      setStage('IDLE');
      setStatusMessage('');
      setConfirmedOrderId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col justify-between p-6 animate-in slide-in-from-right duration-300">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-[#0EA5E9]" />
            <h2 className="text-lg font-bold text-gray-900">Your Shopping Cart</h2>
            <span className="px-2 py-0.5 bg-sky-50 text-[#0EA5E9] font-bold text-xs rounded-full">
              {items.reduce((s, i) => s + i.quantity, 0)} items
            </span>
          </div>
          <button onClick={handleClose} className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-50">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto py-4 space-y-3">
          {stage === 'SUCCESS' ? (
            <div className="py-16 text-center space-y-4">
              <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto" />
              <h3 className="text-xl font-bold text-gray-900">Order Confirmed!</h3>
              <p className="text-sm text-gray-600 max-w-xs mx-auto">{statusMessage}</p>
              <button
                onClick={handleClose}
                className="mt-4 px-6 py-2.5 bg-gray-900 hover:bg-gray-800 text-white text-sm font-semibold rounded-xl"
              >
                Continue Shopping
              </button>
            </div>
          ) : items.length === 0 ? (
            <div className="py-20 text-center space-y-3">
              <ShoppingBag className="w-12 h-12 text-gray-300 mx-auto" />
              <p className="text-sm font-semibold text-gray-700">Your cart is currently empty</p>
              <p className="text-xs text-gray-400">Add products to your cart to checkout with multi-item flash concurrency.</p>
            </div>
          ) : (
            items.map((item) => (
              <div key={item.productId} className="p-3.5 bg-gray-50 rounded-xl border border-gray-200 flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-bold text-gray-900 truncate">{item.title}</h4>
                  <div className="text-xs font-semibold text-emerald-600 mt-0.5">${item.price.toFixed(2)}</div>
                  <div className="text-[10px] text-gray-400">Max in stock: {item.stock}</div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center border border-gray-300 rounded-lg bg-white">
                    <button
                      onClick={() => updateQuantity(item.productId, item.quantity - 1)}
                      className="p-1 text-gray-600 hover:bg-gray-100 rounded-l-md"
                    >
                      <Minus className="w-3 h-3" />
                    </button>
                    <span className="px-2 text-xs font-bold text-gray-800">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.productId, item.quantity + 1)}
                      disabled={item.quantity >= item.stock}
                      className="p-1 text-gray-600 hover:bg-gray-100 rounded-r-md disabled:opacity-40"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>

                  <button
                    onClick={() => removeItem(item.productId)}
                    className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && stage !== 'SUCCESS' && (
          <div className="pt-4 border-t border-gray-100 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-600">Subtotal</span>
              <span className="text-lg font-bold text-gray-900">${totalAmount.toFixed(2)}</span>
            </div>

            {statusMessage && (
              <div className={`p-2.5 rounded-lg text-xs flex items-center gap-2 ${
                stage === 'ERROR' ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-sky-50 text-sky-700 border border-sky-200'
              }`}>
                {stage === 'ERROR' ? <AlertCircle className="w-4 h-4 shrink-0" /> : <Loader2 className="w-4 h-4 animate-spin shrink-0" />}
                <span>{statusMessage}</span>
              </div>
            )}

            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={clearCart}
                disabled={stage === 'CHECKING_OUT' || stage === 'SETTLING_PAYMENT'}
                className="py-2.5 px-3 border border-gray-200 text-gray-700 font-semibold text-xs rounded-xl hover:bg-gray-50"
              >
                Clear Cart
              </button>

              <button
                onClick={handleCheckoutAndPay}
                disabled={stage === 'CHECKING_OUT' || stage === 'SETTLING_PAYMENT'}
                className="py-2.5 px-3 bg-[#0EA5E9] hover:bg-[#0284C7] text-white font-semibold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-60"
              >
                {stage === 'CHECKING_OUT' || stage === 'SETTLING_PAYMENT' ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    Checkout <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
