import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, Banknote, CreditCard, Loader2, MapPin, Smartphone, Wallet } from 'lucide-react';
import { api, apiErrorMessage } from '../api/client.js';
import EmptyState from '../components/EmptyState.jsx';
import { useCart } from '../context/CartContext.jsx';

const money = (value) => value.toLocaleString(undefined, { style: 'currency', currency: 'USD' });

const paymentMethods = [
  { id: 'card', label: 'Card', icon: CreditCard },
  { id: 'upi', label: 'UPI', icon: Smartphone },
  { id: 'wallet', label: 'Wallet', icon: Wallet },
  { id: 'cash', label: 'Cash', icon: Banknote }
];

export default function CheckoutPage() {
  const { restaurant, items, subtotal, clearCart } = useCart();
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: 'Ananya Rao',
    phone: '+91 98765 43210',
    address: '221B Market Street, Koramangala, Bengaluru',
    payment_method: 'card',
    coupon_code: ''
  });

  if (!items.length || !restaurant) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
        <EmptyState title="No order to check out" message="Add menu items before placing an order." />
      </div>
    );
  }

  const deliveryFee = subtotal > 35 ? 0 : restaurant.delivery_fee;
  const platformFee = 1.99;
  const tax = (subtotal + deliveryFee + platformFee) * 0.0825;
  const total = subtotal + deliveryFee + platformFee + tax;

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      const order = await api.placeOrder({
        restaurant_id: restaurant.id,
        customer_id: 'user_demo_001',
        customer: {
          name: form.name,
          phone: form.phone,
          address: form.address
        },
        items: items.map((item) => ({ menu_item_id: item.id, quantity: item.quantity })),
        payment_method: form.payment_method,
        coupon_code: form.coupon_code || undefined
      });
      toast.success('Order placed');
      clearCart();
      navigate(`/track/${order.id}`);
    } catch (err) {
      toast.error(apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_360px] lg:px-8">
      <form onSubmit={submit} className="space-y-5">
        <Link to="/cart" className="inline-flex items-center gap-2 text-sm font-bold text-gray-600 hover:text-gray-950">
          <ArrowLeft size={16} aria-hidden="true" />
          Cart
        </Link>
        <section className="rounded-lg border border-gray-200 bg-white p-5">
          <div className="mb-5 flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-teal-50 text-teal-700">
              <MapPin size={19} aria-hidden="true" />
            </span>
            <div>
              <h1 className="text-2xl font-black text-gray-950">Checkout</h1>
              <p className="text-sm text-gray-600">{restaurant.name}</p>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-bold text-gray-700">
              Name
              <input
                required
                value={form.name}
                onChange={(event) => update('name', event.target.value)}
                className="mt-2 h-11 w-full rounded-md border border-gray-200 px-3 font-medium outline-none focus:border-emerald-500"
              />
            </label>
            <label className="text-sm font-bold text-gray-700">
              Phone
              <input
                required
                value={form.phone}
                onChange={(event) => update('phone', event.target.value)}
                className="mt-2 h-11 w-full rounded-md border border-gray-200 px-3 font-medium outline-none focus:border-emerald-500"
              />
            </label>
            <label className="text-sm font-bold text-gray-700 sm:col-span-2">
              Delivery address
              <textarea
                required
                value={form.address}
                onChange={(event) => update('address', event.target.value)}
                rows={4}
                className="mt-2 w-full rounded-md border border-gray-200 px-3 py-3 font-medium outline-none focus:border-emerald-500"
              />
            </label>
            <label className="text-sm font-bold text-gray-700 sm:col-span-2">
              Coupon
              <input
                value={form.coupon_code}
                onChange={(event) => update('coupon_code', event.target.value.toUpperCase())}
                placeholder="WELCOME50 or DEMO20"
                className="mt-2 h-11 w-full rounded-md border border-gray-200 px-3 font-medium outline-none focus:border-emerald-500"
              />
            </label>
          </div>
        </section>

        <section className="rounded-lg border border-gray-200 bg-white p-5">
          <h2 className="text-lg font-black text-gray-950">Payment Method</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-4">
            {paymentMethods.map((method) => {
              const Icon = method.icon;
              const active = form.payment_method === method.id;
              return (
                <button
                  key={method.id}
                  type="button"
                  onClick={() => update('payment_method', method.id)}
                  className={`flex h-20 flex-col items-center justify-center gap-2 rounded-md border text-sm font-black transition ${
                    active
                      ? 'border-emerald-600 bg-emerald-50 text-emerald-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon size={20} aria-hidden="true" />
                  {method.label}
                </button>
              );
            })}
          </div>
        </section>

        <button
          disabled={submitting}
          className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-rose-600 text-sm font-black text-white hover:bg-rose-700 disabled:cursor-wait disabled:bg-rose-300"
        >
          {submitting && <Loader2 size={18} className="animate-spin" aria-hidden="true" />}
          Place Order
        </button>
      </form>

      <aside className="h-fit rounded-lg border border-gray-200 bg-white p-5 lg:sticky lg:top-24">
        <h2 className="text-lg font-black text-gray-950">Order Summary</h2>
        <div className="mt-4 divide-y divide-gray-100">
          {items.map((item) => (
            <div key={item.id} className="flex justify-between gap-4 py-3 text-sm">
              <div>
                <p className="font-bold text-gray-950">{item.quantity} x {item.name}</p>
                <p className="mt-1 text-gray-500">{item.category}</p>
              </div>
              <p className="font-black text-gray-950">{money(item.price * item.quantity)}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 space-y-3 border-t border-gray-200 pt-4 text-sm">
          <div className="flex justify-between text-gray-600"><span>Subtotal</span><strong className="text-gray-950">{money(subtotal)}</strong></div>
          <div className="flex justify-between text-gray-600"><span>Delivery</span><strong className="text-gray-950">{deliveryFee ? money(deliveryFee) : 'Free'}</strong></div>
          <div className="flex justify-between text-gray-600"><span>Platform fee</span><strong className="text-gray-950">{money(platformFee)}</strong></div>
          <div className="flex justify-between text-gray-600"><span>Tax</span><strong className="text-gray-950">{money(tax)}</strong></div>
          <div className="flex justify-between border-t border-gray-200 pt-3 text-base font-black text-gray-950"><span>Total</span><span>{money(total)}</span></div>
        </div>
      </aside>
    </div>
  );
}

