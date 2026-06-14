import { Minus, Plus } from 'lucide-react';

export default function QuantityControl({ quantity, onChange, compact = false }) {
  const size = compact ? 'h-8 w-8' : 'h-10 w-10';
  return (
    <div className="inline-flex items-center overflow-hidden rounded-md border border-gray-200 bg-white">
      <button
        type="button"
        aria-label="Decrease quantity"
        onClick={() => onChange(quantity - 1)}
        className={`${size} inline-flex items-center justify-center text-gray-700 hover:bg-gray-100`}
      >
        <Minus size={16} aria-hidden="true" />
      </button>
      <span className="min-w-9 text-center text-sm font-bold text-gray-950">{quantity}</span>
      <button
        type="button"
        aria-label="Increase quantity"
        onClick={() => onChange(quantity + 1)}
        className={`${size} inline-flex items-center justify-center text-gray-700 hover:bg-gray-100`}
      >
        <Plus size={16} aria-hidden="true" />
      </button>
    </div>
  );
}

