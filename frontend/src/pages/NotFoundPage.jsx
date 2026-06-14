import { Link } from 'react-router-dom';
import EmptyState from '../components/EmptyState.jsx';

export default function NotFoundPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
      <EmptyState title="Page not found" message="That route is not on the menu." />
      <div className="mt-6 text-center">
        <Link to="/" className="inline-flex h-11 items-center justify-center rounded-md bg-gray-950 px-5 text-sm font-black text-white hover:bg-gray-800">
          Go Home
        </Link>
      </div>
    </div>
  );
}

