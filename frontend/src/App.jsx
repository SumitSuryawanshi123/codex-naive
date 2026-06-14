import { AnimatePresence, motion } from 'framer-motion';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Header from './components/Header.jsx';
import LandingPage from './pages/LandingPage.jsx';
import RestaurantListPage from './pages/RestaurantListPage.jsx';
import RestaurantDetailPage from './pages/RestaurantDetailPage.jsx';
import CartPage from './pages/CartPage.jsx';
import CheckoutPage from './pages/CheckoutPage.jsx';
import TrackingPage from './pages/TrackingPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';

function Page({ children }) {
  return (
    <motion.main
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.18 }}
    >
      {children}
    </motion.main>
  );
}

export default function App() {
  const location = useLocation();
  return (
    <div className="min-h-screen bg-[#f8faf9] text-gray-900">
      <Header />
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<Page><LandingPage /></Page>} />
          <Route path="/restaurants" element={<Page><RestaurantListPage /></Page>} />
          <Route path="/restaurants/:id" element={<Page><RestaurantDetailPage /></Page>} />
          <Route path="/cart" element={<Page><CartPage /></Page>} />
          <Route path="/checkout" element={<Page><CheckoutPage /></Page>} />
          <Route path="/track/:id" element={<Page><TrackingPage /></Page>} />
          <Route path="/orders/:id" element={<Navigate to={`/track/${location.pathname.split('/').pop()}`} replace />} />
          <Route path="*" element={<Page><NotFoundPage /></Page>} />
        </Routes>
      </AnimatePresence>
    </div>
  );
}

