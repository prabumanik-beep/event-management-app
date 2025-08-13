import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import api from '../api'; // We need the configured axios instance

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'));
  const [userProfile, setUserProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true); // Start in a loading state

  const login = () => {
    setIsLoggedIn(true);
    // The useEffect below will now re-run and fetch the profile.
  };

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsLoggedIn(false);
    setUserProfile(null);
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
        const response = await api.get('/profile/');
        setUserProfile(response.data);
        setIsLoggedIn(true);
      } catch (error) {
        logout(); // Token is invalid or expired
      } finally {
        setIsLoading(false);
      }
    };
    verifyAuth();
  }, [logout, isLoggedIn]); // Re-run if isLoggedIn changes (e.g., after login)

  return (
    <AuthContext.Provider value={{ isLoggedIn, userProfile, isLoading, login, logout }}>
      {!isLoading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};