import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Bike, Search, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { api, apiErrorMessage } from '../api/client.js';
import RestaurantCard from '../components/RestaurantCard.jsx';
import { RestaurantGridSkeleton } from '../components/Skeletons.jsx';
import ErrorState from '../components/ErrorState.jsx';

const categoryImages = {
  Pizza: 'https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=400&q=80',
  Burgers: 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=400&q=80',
  Biryani: 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=400&q=80',
  Sushi: 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?auto=format&fit=crop&w=400&q=80',
  Pasta: 'https://images.unsplash.com/photo-1551183053-bf91a1d81141?auto=format&fit=crop&w=400&q=80',
  Noodles: 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=400&q=80',
  Salads: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=400&q=80',
  Tacos: 'https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=400&q=80',
  Desserts: 'https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?auto=format&fit=crop&w=400&q=80',
  Breakfast: 'https://images.unsplash.com/photo-1533089860892-a7c6f0a88666?auto=format&fit=crop&w=400&q=80'
};

export default function LandingPage() {
  const [query, setQuery] = useState('');
  const [featured, setFeatured] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [recommendations, categoryResponse] = await Promise.all([
        api.recommendations({ limit: 8 }),
        api.categories()
      ]);
      setFeatured(recommendations.items);
      setCategories(categoryResponse.items);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submit = (event) => {
    event.preventDefault();
    navigate(`/restaurants${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ''}`);
  };

  return (
    <>
      <section className="hero-image">
        <div className="mx-auto flex min-h-[520px] max-w-7xl flex-col justify-center px-4 py-16 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="max-w-2xl text-white"
          >
            <span className="inline-flex items-center gap-2 rounded-md bg-white/15 px-3 py-2 text-sm font-bold backdrop-blur">
              <Sparkles size={16} aria-hidden="true" />
              Dinner, lunch, snacks, all moving fast
            </span>
            <h1 className="mt-5 text-4xl font-black sm:text-5xl lg:text-6xl">
              CraveCart
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-white/88 sm:text-lg">
              Hot meals from neighborhood favorites, priced clearly and followed from kitchen to doorstep.
            </p>
            <form
              onSubmit={submit}
              className="mt-8 flex w-full max-w-xl flex-col gap-3 rounded-lg bg-white p-2 shadow-soft sm:flex-row"
            >
              <label className="flex min-h-12 flex-1 items-center gap-3 px-3 text-gray-700">
                <Search size={19} aria-hidden="true" />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search restaurants or cravings"
                  className="w-full bg-transparent text-gray-950 outline-none placeholder:text-gray-500"
                />
              </label>
              <button className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-rose-600 px-5 text-sm font-black text-white hover:bg-rose-700">
                Search
                <ArrowRight size={17} aria-hidden="true" />
              </button>
            </form>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-5 flex items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-black text-gray-950">Categories</h2>
            <p className="mt-1 text-sm text-gray-600">Fresh paths into the menu catalog.</p>
          </div>
          <Link to="/restaurants" className="hidden text-sm font-bold text-emerald-700 hover:text-emerald-800 sm:inline-flex">
            View all
          </Link>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {categories.slice(0, 10).map((category) => (
            <Link
              key={category.name}
              to={`/restaurants?category=${encodeURIComponent(category.name)}`}
              className="group relative h-28 overflow-hidden rounded-lg border border-gray-200 bg-gray-100"
            >
              <img
                src={categoryImages[category.name]}
                alt={category.name}
                className="h-full w-full object-cover transition duration-300 group-hover:scale-105"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-gray-950/78 to-gray-950/10" />
              <div className="absolute inset-x-0 bottom-0 p-3 text-white">
                <p className="font-black">{category.name}</p>
                <p className="text-xs text-white/80">{category.count} items</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-14 sm:px-6 lg:px-8">
        <div className="mb-5 flex items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-black text-gray-950">Featured Restaurants</h2>
            <p className="mt-1 text-sm text-gray-600">Popular kitchens with fast handoff times.</p>
          </div>
          <Link to="/restaurants" className="inline-flex items-center gap-2 text-sm font-bold text-emerald-700 hover:text-emerald-800">
            Explore
            <ArrowRight size={16} aria-hidden="true" />
          </Link>
        </div>
        {loading ? (
          <RestaurantGridSkeleton count={8} />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {featured.map((restaurant) => (
              <RestaurantCard key={restaurant.id} restaurant={restaurant} />
            ))}
          </div>
        )}
      </section>
      <section className="border-t border-gray-200 bg-white">
        <div className="mx-auto grid max-w-7xl gap-4 px-4 py-8 sm:grid-cols-3 sm:px-6 lg:px-8">
          {[
            ['100', 'restaurants nearby'],
            ['500', 'dishes ready'],
            ['50', 'drivers on shift']
          ].map(([number, label]) => (
            <div key={label} className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-md bg-teal-50 text-teal-700">
                <Bike size={19} aria-hidden="true" />
              </span>
              <div>
                <p className="text-2xl font-black text-gray-950">{number}</p>
                <p className="text-sm font-medium text-gray-600">{label}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
