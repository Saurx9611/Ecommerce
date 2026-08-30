'use client';

import { useState, useEffect } from 'react';
import { ShoppingBag, RefreshCw, Layers, CheckCircle2, Clock, AlertCircle, XCircle, CreditCard, Loader2 } from 'lucide-react';
import { ordersApi, OrderData } from '@/lib/api/orders';
import { paymentsApi } from '@/lib/api/payments';
import { useAuth } from '@/context/AuthContext';

export default function OrdersHistoryPage() {
  const [orders, setOrders] = useState<OrderData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [payingOrderId, setPayingOrderId] = useState<number | null>(null);
  const { userId } = useAuth();

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ordersApi.list();
      setOrders(data);
    } catch (err: any) {
      console.error('Failed to load orders', err);
      setError('Failed to retrieve order history. Please ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
    const interval = setInterval(loadOrders, 8000);
    return () => clearInterval(interval);
  }, []);

  const handlePayNow = async (orderId: number) => {
    try {
      setPayingOrderId(orderId);
      const paymentKey = `pay-retry-${orderId}-${crypto.randomUUID()}`;
      const res = await paymentsApi.charge({ order_id: orderId }, paymentKey);
      if (res.status === 'PAID') {
        loadOrders();
      }
    } catch (e: any) {
      alert(`Payment failed: ${e?.message || 'Declined'}`);
    } finally {
      setPayingOrderId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PAID':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Settled & Paid
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-50 text-sky-700 border border-sky-200 animate-pulse">
            <Clock className="w-3.5 h-3.5 text-sky-600" /> Processing Payment
          </span>
        );
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertCircle className="w-3.5 h-3.5 text-amber-600" /> Awaiting Payment
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5 text-rose-600" /> Payment Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-[#0EA5E9]" />
            <h1 className="text-2xl font-bold tracking-tight text-[#111827]">Order History & Settlements</h1>
          </div>
          <p className="text-[#6B7280] text-sm mt-1">
            Real-time authoritative orders, line items, and payment settlement tracking for User #{userId || 1}.
          </p>
        </div>
        <button
          onClick={loadOrders}
          disabled={loading}
          className="px-4 py-2 border border-[#E5E7EB] bg-white rounded-xl text-sm font-semibold hover:bg-gray-50 flex items-center gap-2 text-[#111827] shadow-xs self-start"
        >
          <RefreshCw className={`w-4 h-4 text-gray-500 ${loading ? 'animate-spin' : ''}`} />
          Refresh Orders
        </button>
      </div>

      {/* Orders List Container */}
      <div className="bg-white border border-[#E5E7EB] rounded-2xl shadow-xs overflow-hidden">
        
        {loading && orders.length === 0 ? (
          <div className="p-16 text-center space-y-3">
            <Loader2 className="w-8 h-8 text-[#0EA5E9] animate-spin mx-auto" />
            <p className="text-sm font-medium text-gray-500">Retrieving order ledger from PostgreSQL...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center space-y-3">
            <AlertCircle className="w-10 h-10 text-amber-500 mx-auto" />
            <h3 className="text-base font-bold text-gray-900">Failed to Load Orders</h3>
            <p className="text-xs text-gray-500 max-w-md mx-auto">{error}</p>
            <button
              onClick={loadOrders}
              className="mt-2 px-4 py-2 bg-[#0EA5E9] text-white text-xs font-semibold rounded-lg hover:bg-[#0284C7]"
            >
              Retry
            </button>
          </div>
        ) : orders.length === 0 ? (
          <div className="p-16 text-center space-y-3">
            <ShoppingBag className="w-12 h-12 text-gray-300 mx-auto" />
            <h3 className="text-base font-bold text-gray-900">No Orders Found</h3>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              You haven't placed any flash sale orders yet. Explore hardware products and place your first order.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-[#111827]">
              <thead className="bg-gray-50/80 border-b border-[#E5E7EB]">
                <tr>
                  <th scope="col" className="px-6 py-3.5 font-semibold text-[#6B7280] uppercase text-[11px] tracking-wider">Order ID</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold text-[#6B7280] uppercase text-[11px] tracking-wider">Date & Time</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold text-[#6B7280] uppercase text-[11px] tracking-wider">Purchased Items</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold text-[#6B7280] uppercase text-[11px] tracking-wider">Total Amount</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold text-[#6B7280] uppercase text-[11px] tracking-wider">Payment Status</th>
                  <th scope="col" className="px-6 py-3.5 font-semibold text-[#6B7280] uppercase text-[11px] tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E5E7EB]">
                {orders.map((ord) => (
                  <tr key={ord.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs font-bold text-[#0EA5E9]">
                      #{ord.id}
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-600 font-mono">
                      {new Date(ord.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        {ord.items && ord.items.length > 0 ? (
                          ord.items.map((itm) => (
                            <div key={itm.id} className="text-xs text-gray-800 flex items-center gap-1.5">
                              <span className="font-semibold text-gray-900">Product #{itm.product_id}</span>
                              <span className="text-gray-400">×</span>
                              <span className="font-mono font-bold text-sky-600">{itm.quantity}</span>
                              <span className="text-gray-400 font-mono">(${itm.unit_price.toFixed(2)}/ea)</span>
                            </div>
                          ))
                        ) : (
                          <span className="text-xs text-gray-400">Flash item</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-sm text-emerald-600">
                      ${ord.total_amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(ord.status)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {(ord.status === 'PENDING' || ord.status === 'FAILED') ? (
                        <button
                          onClick={() => handlePayNow(ord.id)}
                          disabled={payingOrderId === ord.id}
                          className="px-3 py-1.5 bg-[#0EA5E9] hover:bg-[#0284C7] text-white text-xs font-semibold rounded-lg transition-all shadow-2xs flex items-center gap-1 ml-auto disabled:opacity-60"
                        >
                          {payingOrderId === ord.id ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <CreditCard className="w-3 h-3" />
                          )}
                          Pay Now
                        </button>
                      ) : (
                        <span className="text-xs font-mono text-gray-400">Settled</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </div>
  );
}
