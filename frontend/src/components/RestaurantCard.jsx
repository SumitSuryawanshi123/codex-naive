import { Link } from 'react-router-dom';
import { Clock, Star, Truck } from 'lucide-react';
import { motion } from 'framer-motion';

export default function RestaurantCard({ restaurant, compact = false }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.18 }}
      className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm"
    >
      <Link to={`/restaurants/${restaurant.id}`} className="block">
        <div className={`relative ${compact ? 'h-36' : 'h-44'} overflow-hidden bg-gray-100`}>
          <img
            src={restaurant.image_url}
            alt={restaurant.name}
            className="h-full w-full object-cover transition duration-300 hover:scale-105"
            loading="lazy"
          />
          {restaurant.promoted && (
            <span className="absolute left-3 top-3 rounded-md bg-amber-400 px-2 py-1 text-xs font-bold text-gray-950">
              Featured
            </span>
          )}
        </div>
        <div className="space-y-3 p-4">
          <div>
            <h3 className="text-base font-bold text-gray-950">{restaurant.name}</h3>
            <p className="mt-1 line-clamp-2 text-sm text-gray-600">{restaurant.cuisines.join(', ')}</p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs font-semibold text-gray-700">
            <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-emerald-700">
              <Star size={13} fill="currentColor" aria-hidden="true" />
              {restaurant.rating}
            </span>
            <span className="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1">
              <Clock size={13} aria-hidden="true" />
              {restaurant.delivery_time_min} min
            </span>
            <span className="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1">
              <Truck size={13} aria-hidden="true" />
              ${restaurant.delivery_fee.toFixed(2)}
            </span>
          </div>
        </div>
      </Link>
    </motion.article>
  );
}

