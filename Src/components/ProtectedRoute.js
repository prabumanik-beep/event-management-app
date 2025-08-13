import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = () => {
  const { isLoggedIn } = useAuth();
  if (!isLoggedIn) {
    // If the user is not logged in, redirect them to the login page.
    return <Navigate to="/login" replace />;
  }

  return <Outlet />; // If logged in, render the child route's component.
};

export default ProtectedRoute;