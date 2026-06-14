import { Link, NavLink } from 'react-router-dom';
import { Bike, Home, Menu, Search, ShoppingBag } from 'lucide-react';
import { useCart } from '../context/CartContext.jsx';

const navClass = ({ isActive }) =>
  `hidden rounded-md px-3 py-2 text-sm font-medium transition md:inline-flex ${
    isActive ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-950'
  }`;

export default function Header() {
  const { count } = useCart();

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white/92 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2 text-lg font-black text-gray-950">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-rose-600 text-white">
            <Bike size={20} aria-hidden="true" />
          </span>
          CraveCart
        </Link>
        <nav className="flex items-center gap-1">
          <NavLink to="/" className={navClass}>
            <Home size={16} className="mr-2" aria-hidden="true" />
            Home
          </NavLink>
          <NavLink to="/restaurants" className={navClass}>
            <Search size={16} className="mr-2" aria-hidden="true" />
            Explore
          </NavLink>
          <NavLink
            to="/cart"
            className={({ isActive }) =>
              `relative inline-flex h-10 items-center gap-2 rounded-md px-3 text-sm font-semibold transition ${
                isActive
                  ? 'bg-emerald-600 text-white'
                  : 'bg-gray-950 text-white hover:bg-gray-800'
              }`
            }
          >
            <ShoppingBag size={18} aria-hidden="true" />
            <span className="hidden sm:inline">Cart</span>
            <span className="inline-flex min-w-5 justify-center rounded-full bg-white px-1.5 text-xs font-bold text-gray-950">
              {count}
            </span>
          </NavLink>
          <NavLink to="/restaurants" className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-gray-200 text-gray-700 md:hidden">
            <Menu size={18} aria-hidden="true" />
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

