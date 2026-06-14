import { Bike, MapPin } from 'lucide-react';

export default function RouteMap({ route = [], progress = 0 }) {
  const points = route.length ? route : [];
  const current = Math.min(4, Math.max(0, Math.round((progress / 100) * 4)));

  return (
    <div className="map-grid relative min-h-72 overflow-hidden rounded-lg border border-teal-100 bg-teal-50">
      <div className="absolute inset-6">
        <div className="absolute left-8 right-8 top-1/2 h-1 -translate-y-1/2 rounded-full bg-teal-200" />
        <div
          className="absolute left-8 top-1/2 h-1 -translate-y-1/2 rounded-full bg-teal-600 transition-all duration-700"
          style={{ width: `calc((100% - 4rem) * ${progress / 100})` }}
        />
        {Array.from({ length: 5 }).map((_, index) => (
          <div
            key={index}
            className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${index * 25}%` }}
          >
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                index <= current
                  ? 'border-teal-700 bg-teal-600 text-white'
                  : 'border-teal-200 bg-white text-teal-700'
              }`}
            >
              {index === current ? <Bike size={18} aria-hidden="true" /> : <MapPin size={17} aria-hidden="true" />}
            </div>
            <p className="mt-3 w-20 -translate-x-5 text-center text-xs font-bold text-gray-700">
              {points[index]?.label || ['Store', 'Lane', 'Road', 'Lane', 'You'][index]}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

