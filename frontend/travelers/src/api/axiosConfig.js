import axios from 'axios';

// URL del backend. En producción se define en frontend/travelers/.env:
// VITE_API_URL=https://api.tudominio.com
export const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

// Los archivos subidos llegan como "/uploads/..."; las fotos de Google ya son URLs completas
export function mediaUrl(url) {
  if (!url) return null;
  return url.startsWith('/') ? `${API_URL}${url}` : url;
}

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;
