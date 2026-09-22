import { createContext, useContext, useEffect, useState } from 'react';

import api from '../api/axiosConfig';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(false);

  const isAuthenticated = Boolean(token);

  const getCurrentUser = async () => {
    if (!token) {
      setUser(null);
      return;
    }

    setLoadingUser(true);

    try {
      const response = await api.get('/users/me');
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
    } finally {
      setLoadingUser(false);
    }
  };

  const login = async (newToken) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    getCurrentUser();
  }, [token]);

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        loadingUser,
        isAuthenticated,
        login,
        logout,
        getCurrentUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}