export function RestaurantGridSkeleton({ count = 8 }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <div className="h-44 animate-pulse bg-gray-200" />
          <div className="space-y-3 p-4">
            <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200" />
            <div className="h-3 w-1/2 animate-pulse rounded bg-gray-200" />
            <div className="flex gap-2">
              <div className="h-7 w-16 animate-pulse rounded bg-gray-200" />
              <div className="h-7 w-20 animate-pulse rounded bg-gray-200" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function MenuSkeleton() {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {Array.from({ length: 8 }).map((_, index) => (
        <div key={index} className="flex gap-4 rounded-lg border border-gray-200 bg-white p-4">
          <div className="h-24 w-24 animate-pulse rounded-md bg-gray-200" />
          <div className="flex-1 space-y-3">
            <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200" />
            <div className="h-3 w-full animate-pulse rounded bg-gray-200" />
            <div className="h-3 w-1/2 animate-pulse rounded bg-gray-200" />
          </div>
        </div>
      ))}
    </div>
  );
}

