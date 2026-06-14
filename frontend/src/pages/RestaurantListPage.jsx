import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Filter, Search, SlidersHorizontal, X } from 'lucide-react';
import { api, apiErrorMessage } from '../api/client.js';
import EmptyState from '../components/EmptyState.jsx';
import ErrorState from '../components/ErrorState.jsx';
import RestaurantCard from '../components/RestaurantCard.jsx';
import { RestaurantGridSkeleton } from '../components/Skeletons.jsx';

export default function RestaurantListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [restaurants, setRestaurants] = useState([]);
  const [categories, setCategories] = useState([]);
  const [cuisines, setCuisines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const filters = useMemo(
    () => ({
      q: searchParams.get('q') || '',
      category: searchParams.get('category') || '',
      cuisine: searchParams.get('cuisine') || '',
      min_rating: searchParams.get('min_rating') || '',
      sort_by: searchParams.get('sort_by') || 'recommended'
    }),
    [searchParams]
  );

  const updateFilter = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next);
  };

  const clearFilters = () => {
    setQuery('');
    setSearchParams({});
  };

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [restaurantResponse, categoryResponse] = await Promise.all([
        api.restaurants({
          q: filters.q,
          category: filters.category || undefined,
          cuisine: filters.cuisine || undefined,
          min_rating: filters.min_rating || undefined,
          sort_by: filters.sort_by,
          limit: 48
        }),
        api.categories()
      ]);
      setRestaurants(restaurantResponse.items);
      setCategories(categoryResponse.items);
      setCuisines(categoryResponse.cuisines);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [filters.category, filters.cuisine, filters.min_rating, filters.q, filters.sort_by]);

  useEffect(() => {
    setQuery(filters.q);
    load();
  }, [filters.q, load]);

  const submit = (event) => {
    event.preventDefault();
    updateFilter('q', query.trim());
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-sm font-bold uppercase text-rose-600">Explore</p>
          <h1 className="mt-1 text-3xl font-black text-gray-950">Restaurants</h1>
          <p className="mt-2 max-w-2xl text-sm text-gray-600">
            Search menus, compare ratings, and find a kitchen that can move right now.
          </p>
        </div>
        <form onSubmit={submit} className="flex w-full max-w-xl overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <label className="flex h-12 flex-1 items-center gap-3 px-4">
            <Search size={18} className="text-gray-500" aria-hidden="true" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Restaurant, cuisine, neighborhood"
              className="w-full outline-none"
            />
          </label>
          <button className="inline-flex h-12 items-center justify-center bg-gray-950 px-5 text-sm font-bold text-white hover:bg-gray-800">
            Search
          </button>
        </form>
      </div>

      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div className="inline-flex items-center gap-2 text-sm font-black text-gray-950">
            <SlidersHorizontal size={18} aria-hidden="true" />
            Filters
          </div>
          <button
            onClick={clearFilters}
            className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-bold text-gray-600 hover:bg-gray-100"
          >
            <X size={16} aria-hidden="true" />
            Clear
          </button>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <select
            value={filters.category}
            onChange={(event) => updateFilter('category', event.target.value)}
            className="h-11 rounded-md border border-gray-200 bg-white px-3 text-sm font-medium outline-none focus:border-emerald-500"
          >
            <option value="">All categories</option>
            {categories.map((category) => (
              <option key={category.name} value={category.name}>
                {category.name}
              </option>
            ))}
          </select>
          <select
            value={filters.cuisine}
            onChange={(event) => updateFilter('cuisine', event.target.value)}
            className="h-11 rounded-md border border-gray-200 bg-white px-3 text-sm font-medium outline-none focus:border-emerald-500"
          >
            <option value="">All cuisines</option>
            {cuisines.map((cuisine) => (
              <option key={cuisine} value={cuisine}>
                {cuisine}
              </option>
            ))}
          </select>
          <select
            value={filters.min_rating}
            onChange={(event) => updateFilter('min_rating', event.target.value)}
            className="h-11 rounded-md border border-gray-200 bg-white px-3 text-sm font-medium outline-none focus:border-emerald-500"
          >
            <option value="">Any rating</option>
            <option value="4.0">4.0+</option>
            <option value="4.3">4.3+</option>
            <option value="4.6">4.6+</option>
          </select>
          <select
            value={filters.sort_by}
            onChange={(event) => updateFilter('sort_by', event.target.value)}
            className="h-11 rounded-md border border-gray-200 bg-white px-3 text-sm font-medium outline-none focus:border-emerald-500"
          >
            <option value="recommended">Recommended</option>
            <option value="rating">Rating</option>
            <option value="delivery_time">Fastest</option>
            <option value="delivery_fee">Lowest fee</option>
          </select>
          <div className="flex h-11 items-center gap-2 rounded-md bg-emerald-50 px-3 text-sm font-bold text-emerald-800">
            <Filter size={16} aria-hidden="true" />
            {restaurants.length} visible
          </div>
        </div>
      </div>

      {loading ? (
        <RestaurantGridSkeleton count={12} />
      ) : error ? (
        <ErrorState message={error} onRetry={load} />
      ) : restaurants.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {restaurants.map((restaurant) => (
            <RestaurantCard key={restaurant.id} restaurant={restaurant} />
          ))}
        </div>
      ) : (
        <EmptyState title="No restaurants found" message="Try a broader cuisine, category, or rating filter." />
      )}
    </div>
  );
}
