import { Plus, Timer } from 'lucide-react';
import { motion } from 'framer-motion';

export default function MenuItemCard({ item, onAdd }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-4 rounded-lg border border-gray-200 bg-white p-4"
    >
      <img
        src={item.image_url}
        alt={item.name}
        className="h-24 w-24 flex-none rounded-md object-cover sm:h-28 sm:w-28"
        loading="lazy"
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-bold text-gray-950">{item.name}</h3>
            <p className="mt-1 line-clamp-2 text-sm text-gray-600">{item.description}</p>
          </div>
          <span className="rounded-md bg-gray-100 px-2 py-1 text-xs font-bold text-gray-700">
            {item.spice_level}
          </span>
        </div>
        <div className="mt-auto flex items-end justify-between gap-3 pt-4">
          <div>
            <p className="text-base font-black text-gray-950">${item.price.toFixed(2)}</p>
            <p className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-gray-500">
              <Timer size={13} aria-hidden="true" />
              {item.prep_time_min} min
            </p>
          </div>
          <button
            onClick={() => onAdd(item)}
            disabled={!item.available}
            className="inline-flex h-10 items-center gap-2 rounded-md bg-emerald-600 px-3 text-sm font-bold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-gray-300"
          >
            <Plus size={16} aria-hidden="true" />
            Add
          </button>
        </div>
      </div>
    </motion.article>
  );
}

