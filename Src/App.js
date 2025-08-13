import React, { useState } from 'react';
import { Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom';
import Login from './components/Login';
import Profile from './components/Profile';
import './styles/App.css'; // Import the new CSS file

function App() {
  // A simple check for an auth token to determine if the user is logged in.
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('access_token'));
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setIsLoggedIn(false);
    navigate('/login'); // Explicitly navigate to login page after logout
  };

  return (
    <div>
      <nav>
        {isLoggedIn ? (
          <>
            <Link to="/profile">Profile</Link> | <button onClick={handleLogout} className="nav-logout-button">Logout</button>
          </>
        ) : (
          <Link to="/login">Login</Link>
        )}
      </nav>
      <hr />
      <Routes>
        <Route path="/login" element={<Login onLoginSuccess={() => setIsLoggedIn(true)} />} />
        <Route path="/profile" element={isLoggedIn ? <Profile /> : <Navigate to="/login" />} />
        <Route path="*" element={<Navigate to={isLoggedIn ? "/profile" : "/login"} />} />
      </Routes>
    </div>
  );
}

export default App;