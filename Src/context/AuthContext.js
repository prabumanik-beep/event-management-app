import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import api from '../api'; // We need the configured axios instance

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'));
  const [isLoading, setIsLoading] = useState(true); // Start in a loading state

  const login = () => {
    setIsLoggedIn(true);
  };

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsLoggedIn(false);
  }, []);

  useEffect(() => {
    const verifyAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        // A lightweight request to verify the token is still valid.
        await api.get('/profile/');
        setIsLoggedIn(true);
      } catch (error) {
        logout(); // Token is invalid or expired
      } finally {
        setIsLoading(false);
      }
    };
    verifyAuth();
  }, [logout]);

  return (
    <AuthContext.Provider value={{ isLoggedIn, isLoading, login, logout }}>
      {!isLoading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};