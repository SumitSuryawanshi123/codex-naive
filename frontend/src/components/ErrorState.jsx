import { AlertTriangle, RefreshCcw } from 'lucide-react';

export default function ErrorState({ message = 'Could not load this view.', onRetry }) {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center rounded-lg border border-rose-200 bg-rose-50 p-8 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-md bg-white text-rose-600">
        <AlertTriangle size={24} aria-hidden="true" />
      </div>
      <h3 className="text-lg font-bold text-gray-950">Something broke</h3>
      <p className="mt-2 max-w-md text-sm text-rose-800">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 inline-flex items-center gap-2 rounded-md bg-rose-600 px-4 py-2 text-sm font-bold text-white hover:bg-rose-700"
        >
          <RefreshCcw size={16} aria-hidden="true" />
          Retry
        </button>
      )}
    </div>
  );
}

