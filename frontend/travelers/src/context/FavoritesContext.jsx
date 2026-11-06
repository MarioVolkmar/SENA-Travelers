import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import api from '../api/axiosConfig';
import { useAuth } from './AuthContext';

const FavoritesContext = createContext({ ids: new Set(), isFavorite: () => false, toggle: async () => {} });

/** Paquetes guardados del usuario, compartidos por todas las tarjetas. */
export function FavoritesProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [ids, setIds] = useState(() => new Set());

  useEffect(() => {
    if (!isAuthenticated) {
      setIds(new Set());
      return;
    }
    api.get('/favorites/ids')
      .then((response) => setIds(new Set(response.data)))
      .catch(() => setIds(new Set()));
  }, [isAuthenticated]);

  const isFavorite = useCallback((id) => ids.has(id), [ids]);

  const toggle = useCallback(async (id) => {
    const adding = !ids.has(id);
    // Respuesta inmediata en pantalla; si falla se revierte
    setIds((current) => {
      const next = new Set(current);
      if (adding) next.add(id); else next.delete(id);
      return next;
    });
    try {
      const response = adding ? await api.post(`/favorites/${id}`) : await api.delete(`/favorites/${id}`);
      setIds(new Set(response.data));
    } catch {
      setIds((current) => {
        const next = new Set(current);
        if (adding) next.delete(id); else next.add(id);
        return next;
      });
    }
  }, [ids]);

  const value = useMemo(() => ({ ids, isFavorite, toggle }), [ids, isFavorite, toggle]);

  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useFavorites() {
  return useContext(FavoritesContext);
}
