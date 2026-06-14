import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Bike, CheckCircle2, Clock, MapPin, PackageCheck, RefreshCcw, Store } from 'lucide-react';
import { api, apiErrorMessage } from '../api/client.js';
import ErrorState from '../components/ErrorState.jsx';
import RouteMap from '../components/RouteMap.jsx';

const statusLabel = {
  pricing_confirmed: 'Pricing confirmed',
  payment_captured: 'Payment captured',
  confirmed: 'Confirmed',
  assigned: 'Driver assigned',
  arrived: 'Driver at restaurant',
  picked_up: 'Picked up',
  nearby: 'Almost there',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  delivery_allocation_failed: 'Driver allocation failed',
  unavailable: 'Tracking unavailable'
};

const steps = [
  { id: 'confirmed', label: 'Confirmed', icon: CheckCircle2 },
  { id: 'assigned', label: 'Driver', icon: Bike },
  { id: 'arrived', label: 'Pickup', icon: Store },
  { id: 'picked_up', label: 'On route', icon: PackageCheck },
  { id: 'delivered', label: 'Delivered', icon: MapPin }
];

const stepIndex = (status) => {
  if (status === 'delivered') return 4;
  if (status === 'nearby' || status === 'picked_up') return 3;
  if (status === 'arrived') return 2;
  if (status === 'assigned') return 1;
  return 0;
};

export default function TrackingPage() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);
  const [tracking, setTracking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setError('');
    try {
      const [orderResponse, trackingResponse] = await Promise.all([
        api.order(id),
        api.tracking(id)
      ]);
      setOrder(orderResponse);
      setTracking(trackingResponse);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
    const interval = window.setInterval(load, 5000);
    return () => window.clearInterval(interval);
  }, [load]);

  if (loading && !order) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="h-80 animate-pulse rounded-lg bg-gray-200" />
      </div>
    );
  }

  if (error && !order) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
        <ErrorState message={error} onRetry={load} />
      </div>
    );
  }

  const currentStatus = tracking?.status || order?.tracking?.status || order?.status || 'confirmed';
  const progress = tracking?.progress ?? order?.tracking?.progress ?? 10;
  const eta = tracking?.eta_minutes ?? order?.tracking?.eta_minutes ?? 0;
  const activeIndex = stepIndex(currentStatus);
  const restaurant = order.restaurant || { name: order.restaurant_name };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-bold uppercase text-rose-600">Order {id}</p>
          <h1 className="mt-1 text-3xl font-black text-gray-950">{statusLabel[currentStatus] || currentStatus}</h1>
          <p className="mt-2 text-sm text-gray-600">{restaurant?.name}</p>
        </div>
        <button
          onClick={load}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-md border border-gray-200 bg-white px-4 text-sm font-bold text-gray-700 hover:bg-gray-50"
        >
          <RefreshCcw size={16} aria-hidden="true" />
          Refresh
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <section className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-5">
            <div className="mb-5 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-black text-gray-950">Delivery Progress</h2>
                <p className="mt-1 text-sm text-gray-600">{progress}% complete</p>
              </div>
              <div className="flex h-12 items-center gap-2 rounded-md bg-amber-50 px-4 text-amber-800">
                <Clock size={18} aria-hidden="true" />
                <span className="text-sm font-black">{eta ? `${eta} min` : 'Now'}</span>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-5">
              {steps.map((step, index) => {
                const Icon = step.icon;
                const active = index <= activeIndex;
                return (
                  <div key={step.id} className={`rounded-lg border p-3 ${active ? 'border-emerald-200 bg-emerald-50' : 'border-gray-200 bg-white'}`}>
                    <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-md ${active ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-500'}`}>
                      <Icon size={17} aria-hidden="true" />
                    </div>
                    <p className="text-sm font-black text-gray-950">{step.label}</p>
                  </div>
                );
              })}
            </div>
          </div>

          <RouteMap route={tracking?.route || order?.tracking?.route || []} progress={progress} />
        </section>

        <aside className="h-fit rounded-lg border border-gray-200 bg-white p-5 lg:sticky lg:top-24">
          <h2 className="text-lg font-black text-gray-950">Order Details</h2>
          {tracking?.driver && (
            <div className="mt-4 rounded-lg bg-gray-50 p-4">
              <p className="text-sm font-bold text-gray-500">Driver</p>
              <p className="mt-1 font-black text-gray-950">{tracking.driver.name}</p>
              <p className="mt-1 text-sm text-gray-600">{tracking.driver.vehicle} · {tracking.driver.rating} rating</p>
            </div>
          )}
          <div className="mt-4 divide-y divide-gray-100">
            {(order.items || []).map((item) => (
              <div key={item.id} className="flex justify-between gap-4 py-3 text-sm">
                <span className="font-bold text-gray-700">{item.quantity} x {item.name}</span>
                <span className="font-black text-gray-950">${Number(item.line_total || item.price * item.quantity).toFixed(2)}</span>
              </div>
            ))}
          </div>
          {order.totals && (
            <div className="mt-4 flex justify-between border-t border-gray-200 pt-4 text-base font-black text-gray-950">
              <span>Total</span>
              <span>${Number(order.totals.total).toFixed(2)}</span>
            </div>
          )}
          <Link
            to="/restaurants"
            className="mt-5 inline-flex h-11 w-full items-center justify-center rounded-md bg-gray-950 text-sm font-black text-white hover:bg-gray-800"
          >
            Order Again
          </Link>
        </aside>
      </div>
    </div>
  );
}
