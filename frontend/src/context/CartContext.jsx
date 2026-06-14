import { createContext, useContext, useMemo, useReducer } from 'react';
import toast from 'react-hot-toast';

const CartContext = createContext(null);
const STORAGE_KEY = 'cravecart.cart.v1';

const loadCart = () => {
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY)) || { restaurant: null, items: [] };
  } catch {
    return { restaurant: null, items: [] };
  }
};

const persist = (state) => {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
};

const reducer = (state, action) => {
  switch (action.type) {
    case 'ADD_ITEM': {
      const { restaurant, item } = action.payload;
      const shouldReset = state.restaurant && state.restaurant.id !== restaurant.id;
      const base = shouldReset ? { restaurant, items: [] } : { ...state, restaurant };
      const existing = base.items.find((cartItem) => cartItem.id === item.id);
      const items = existing
        ? base.items.map((cartItem) =>
            cartItem.id === item.id
              ? { ...cartItem, quantity: Math.min(cartItem.quantity + 1, 20) }
              : cartItem
          )
        : [...base.items, { ...item, quantity: 1 }];
      const next = { restaurant, items };
      persist(next);
      if (shouldReset) toast('Cart switched to this restaurant');
      return next;
    }
    case 'SET_QTY': {
      const items = state.items
        .map((item) =>
          item.id === action.payload.id
            ? { ...item, quantity: Math.max(0, Math.min(action.payload.quantity, 20)) }
            : item
        )
        .filter((item) => item.quantity > 0);
      const next = { restaurant: items.length ? state.restaurant : null, items };
      persist(next);
      return next;
    }
    case 'REMOVE_ITEM': {
      const items = state.items.filter((item) => item.id !== action.payload);
      const next = { restaurant: items.length ? state.restaurant : null, items };
      persist(next);
      return next;
    }
    case 'CLEAR': {
      const next = { restaurant: null, items: [] };
      persist(next);
      return next;
    }
    default:
      return state;
  }
};

export const CartProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, undefined, loadCart);
  const subtotal = state.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const count = state.items.reduce((sum, item) => sum + item.quantity, 0);
  const value = useMemo(
    () => ({
      ...state,
      subtotal,
      count,
      addItem: (restaurant, item) => dispatch({ type: 'ADD_ITEM', payload: { restaurant, item } }),
      setQuantity: (id, quantity) => dispatch({ type: 'SET_QTY', payload: { id, quantity } }),
      removeItem: (id) => dispatch({ type: 'REMOVE_ITEM', payload: id }),
      clearCart: () => dispatch({ type: 'CLEAR' })
    }),
    [state, subtotal, count]
  );
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

export const useCart = () => {
  const value = useContext(CartContext);
  if (!value) throw new Error('useCart must be used inside CartProvider');
  return value;
};

