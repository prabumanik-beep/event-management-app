import React from 'react';
import { Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom';
import Login from './components/Login';
import Profile from './components/Profile';
import ProtectedRoute from './components/ProtectedRoute';
import styles from './App.module.css';
import { useAuth } from './context/AuthContext';

function App() {
  const { isLoggedIn, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div>
      <nav>
        {isLoggedIn ? (
          <>
            <Link to="/profile">Profile</Link> | <button onClick={handleLogout} className={styles.navLogoutButton}>Logout</button>
          </>
        ) : (
          <Link to="/login">Login</Link>
        )}
      </nav>
      <hr />
      <Routes>
        {/* If user is logged in, /login redirects to /profile. Otherwise, show Login page. */}
        <Route path="/login" element={isLoggedIn ? <Navigate to="/profile" /> : <Login />} />

        {/* Protected Routes are nested inside the ProtectedRoute component */}
        <Route element={<ProtectedRoute />}>
          <Route path="/profile" element={<Profile />} />
        </Route>

        <Route path="*" element={<Navigate to={isLoggedIn ? '/profile' : '/login'} />} />
      </Routes>
    </div>
  );
}

export default App;