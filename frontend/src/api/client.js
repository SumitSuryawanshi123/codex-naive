import axios from 'axios';

export const restaurantApi = axios.create({
  baseURL: import.meta.env.VITE_RESTAURANT_API_URL || 'http://localhost:8001',
  timeout: 10000
});

const messageFromError = (error) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.detail) return detail.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg).join(', ');
  if (error.code === 'ECONNABORTED') return 'The request timed out';
  return 'Something went wrong';
};

export const apiErrorMessage = messageFromError;

export const api = {
  restaurants: (params) => restaurantApi.get('/restaurants', { params }).then((res) => res.data),
  restaurant: (id) => restaurantApi.get(`/restaurants/${id}`).then((res) => res.data),
  menu: (id, params) => restaurantApi.get(`/restaurants/${id}/menu`, { params }).then((res) => res.data),
  categories: () => restaurantApi.get('/categories').then((res) => res.data),
  recommendations: (params) => restaurantApi.get('/recommendations', { params }).then((res) => res.data),
  searchMenu: (params) => restaurantApi.get('/search/menu', { params }).then((res) => res.data),
  placeOrder: (payload) => restaurantApi.post('/orders', payload).then((res) => res.data),
  order: (id) => restaurantApi.get(`/orders/${id}`).then((res) => res.data),
  tracking: (id) => restaurantApi.get(`/orders/${id}/tracking`).then((res) => res.data)
};

