import { Link } from 'react-router-dom';
import { ArrowLeft, CreditCard, Trash2 } from 'lucide-react';
import EmptyState from '../components/EmptyState.jsx';
import QuantityControl from '../components/QuantityControl.jsx';
import { useCart } from '../context/CartContext.jsx';

const money = (value) => value.toLocaleString(undefined, { style: 'currency', currency: 'USD' });

export default function CartPage() {
  const { restaurant, items, subtotal, setQuantity, removeItem } = useCart();
  const deliveryFee = restaurant ? (subtotal > 35 ? 0 : restaurant.delivery_fee) : 0;
  const platformFee = items.length ? 1.99 : 0;
  const tax = (subtotal + deliveryFee + platformFee) * 0.0825;
  const total = subtotal + deliveryFee + platformFee + tax;

  if (!items.length) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
        <EmptyState title="Your cart is empty" message="Pick a restaurant and build an order." />
        <div className="mt-6 text-center">
          <Link to="/restaurants" className="inline-flex h-11 items-center justify-center rounded-md bg-rose-600 px-5 text-sm font-black text-white hover:bg-rose-700">
            Browse Restaurants
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_360px] lg:px-8">
      <div>
        <Link to={`/restaurants/${restaurant.id}`} className="mb-5 inline-flex items-center gap-2 text-sm font-bold text-gray-600 hover:text-gray-950">
          <ArrowLeft size={16} aria-hidden="true" />
          {restaurant.name}
        </Link>
        <div className="rounded-lg border border-gray-200 bg-white">
          <div className="border-b border-gray-200 p-5">
            <h1 className="text-2xl font-black text-gray-950">Cart</h1>
            <p className="mt-1 text-sm text-gray-600">{items.length} item{items.length === 1 ? '' : 's'} from {restaurant.name}</p>
          </div>
          <div className="divide-y divide-gray-100">
            {items.map((item) => (
              <div key={item.id} className="grid gap-4 p-4 sm:grid-cols-[80px_1fr_auto] sm:items-center">
                <img src={item.image_url} alt={item.name} className="h-20 w-20 rounded-md object-cover" />
                <div>
                  <p className="font-bold text-gray-950">{item.name}</p>
                  <p className="mt-1 text-sm text-gray-600">{item.category}</p>
                  <p className="mt-2 text-sm font-black text-gray-950">{money(item.price)}</p>
                </div>
                <div className="flex items-center justify-between gap-3 sm:justify-end">
                  <QuantityControl quantity={item.quantity} onChange={(quantity) => setQuantity(item.id, quantity)} compact />
                  <button
                    onClick={() => removeItem(item.id)}
                    aria-label={`Remove ${item.name}`}
                    className="inline-flex h-9 w-9 items-center justify-center rounded-md text-gray-500 hover:bg-rose-50 hover:text-rose-600"
                  >
                    <Trash2 size={17} aria-hidden="true" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <aside className="h-fit rounded-lg border border-gray-200 bg-white p-5 lg:sticky lg:top-24">
        <h2 className="text-lg font-black text-gray-950">Order Summary</h2>
        <div className="mt-5 space-y-3 text-sm">
          <div className="flex justify-between text-gray-600">
            <span>Subtotal</span>
            <span className="font-bold text-gray-950">{money(subtotal)}</span>
          </div>
          <div className="flex justify-between text-gray-600">
            <span>Delivery</span>
            <span className="font-bold text-gray-950">{deliveryFee ? money(deliveryFee) : 'Free'}</span>
          </div>
          <div className="flex justify-between text-gray-600">
            <span>Platform fee</span>
            <span className="font-bold text-gray-950">{money(platformFee)}</span>
          </div>
          <div className="flex justify-between text-gray-600">
            <span>Tax</span>
            <span className="font-bold text-gray-950">{money(tax)}</span>
          </div>
          <div className="border-t border-gray-200 pt-3">
            <div className="flex justify-between text-base font-black text-gray-950">
              <span>Total</span>
              <span>{money(total)}</span>
            </div>
          </div>
        </div>
        <Link
          to="/checkout"
          className="mt-5 inline-flex h-12 w-full items-center justify-center gap-2 rounded-md bg-emerald-600 text-sm font-black text-white hover:bg-emerald-700"
        >
          <CreditCard size={17} aria-hidden="true" />
          Checkout
        </Link>
      </aside>
    </div>
  );
}

