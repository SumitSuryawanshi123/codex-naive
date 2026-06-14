import { SearchX } from 'lucide-react';

export default function EmptyState({ title = 'Nothing here yet', message = 'Try a different search or filter.' }) {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white p-8 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-md bg-gray-100 text-gray-600">
        <SearchX size={24} aria-hidden="true" />
      </div>
      <h3 className="text-lg font-bold text-gray-950">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-gray-600">{message}</p>
    </div>
  );
}

