import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, Clock, Search, ShoppingBag, Star, Truck } from 'lucide-react';
import { api, apiErrorMessage } from '../api/client.js';
import ErrorState from '../components/ErrorState.jsx';
import MenuItemCard from '../components/MenuItemCard.jsx';
import { MenuSkeleton } from '../components/Skeletons.jsx';
import { useCart } from '../context/CartContext.jsx';

export default function RestaurantDetailPage() {
  const { id } = useParams();
  const { addItem, count, restaurant: cartRestaurant } = useCart();
  const [restaurant, setRestaurant] = useState(null);
  const [menu, setMenu] = useState({ items: [], groups: {} });
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const categories = useMemo(() => Object.keys(menu.groups || {}), [menu.groups]);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [restaurantResponse, menuResponse] = await Promise.all([
        api.restaurant(id),
        api.menu(id, { q: query || undefined, category: category || undefined })
      ]);
      setRestaurant(restaurantResponse);
      setMenu(menuResponse);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [category, id, query]);

  useEffect(() => {
    const timer = setTimeout(load, 180);
    return () => clearTimeout(timer);
  }, [load]);

  const handleAdd = (item) => {
    addItem(restaurant, item);
    toast.success(`${item.name} added`);
  };

  if (loading && !restaurant) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <MenuSkeleton />
      </div>
    );
  }

  if (error && !restaurant) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <ErrorState message={error} onRetry={load} />
      </div>
    );
  }

  return (
    <div>
      <section className="relative min-h-[320px] overflow-hidden bg-gray-950">
        <img
          src={restaurant.image_url}
          alt={restaurant.name}
          className="absolute inset-0 h-full w-full object-cover opacity-60"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-gray-950 via-gray-950/72 to-gray-950/25" />
        <div className="relative mx-auto flex min-h-[320px] max-w-7xl flex-col justify-end px-4 py-8 text-white sm:px-6 lg:px-8">
          <Link to="/restaurants" className="mb-auto inline-flex w-fit items-center gap-2 rounded-md bg-white/12 px-3 py-2 text-sm font-bold backdrop-blur hover:bg-white/20">
            <ArrowLeft size={16} aria-hidden="true" />
            Restaurants
          </Link>
          <div className="max-w-2xl">
            <p className="text-sm font-bold uppercase text-amber-300">{restaurant.neighborhood}</p>
            <h1 className="mt-2 text-4xl font-black sm:text-5xl">{restaurant.name}</h1>
            <p className="mt-3 text-white/82">{restaurant.description}</p>
            <div className="mt-5 flex flex-wrap gap-2 text-sm font-bold">
              <span className="inline-flex items-center gap-1 rounded-md bg-white px-3 py-2 text-gray-950">
                <Star size={16} fill="currentColor" aria-hidden="true" />
                {restaurant.rating}
              </span>
              <span className="inline-flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 backdrop-blur">
                <Clock size={16} aria-hidden="true" />
                {restaurant.delivery_time_min} min
              </span>
              <span className="inline-flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 backdrop-blur">
                <Truck size={16} aria-hidden="true" />
                ${restaurant.delivery_fee.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1fr_320px] lg:px-8">
        <div>
          <div className="mb-5 flex flex-col gap-3 rounded-lg border border-gray-200 bg-white p-4 sm:flex-row">
            <label className="flex h-11 flex-1 items-center gap-3 rounded-md border border-gray-200 px-3">
              <Search size={17} className="text-gray-500" aria-hidden="true" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search this menu"
                className="w-full outline-none"
              />
            </label>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              className="h-11 rounded-md border border-gray-200 bg-white px-3 text-sm font-bold outline-none"
            >
              <option value="">All categories</option>
              {categories.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </div>
          {loading ? (
            <MenuSkeleton />
          ) : (
            <div className="space-y-8">
              {Object.entries(menu.groups).map(([group, items]) => (
                <div key={group}>
                  <h2 className="mb-3 text-xl font-black text-gray-950">{group}</h2>
                  <div className="grid gap-4 lg:grid-cols-2">
                    {items.map((item) => (
                      <MenuItemCard key={item.id} item={item} onAdd={handleAdd} />
                    ))}
                  </div>
                </div>
              ))}
              {!menu.items.length && (
                <div className="rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center text-sm font-medium text-gray-600">
                  No matching menu items.
                </div>
              )}
            </div>
          )}
        </div>
        <aside className="h-fit rounded-lg border border-gray-200 bg-white p-4 lg:sticky lg:top-24">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-50 text-emerald-700">
              <ShoppingBag size={18} aria-hidden="true" />
            </span>
            <div>
              <p className="text-sm font-bold text-gray-950">Cart</p>
              <p className="text-xs text-gray-500">
                {cartRestaurant?.id === restaurant.id ? `${count} item${count === 1 ? '' : 's'}` : 'Ready for this menu'}
              </p>
            </div>
          </div>
          <Link
            to="/cart"
            className="mt-4 inline-flex h-11 w-full items-center justify-center rounded-md bg-gray-950 text-sm font-black text-white hover:bg-gray-800"
          >
            Review Order
          </Link>
        </aside>
      </section>
    </div>
  );
}
