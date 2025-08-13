import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Profile from './components/Profile';
import Meetings from './components/Meetings';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import { useAuth } from './context/AuthContext';

function App() {
  const { isLoggedIn } = useAuth();

  return (
    <div>
      <Navbar />
      <main className="container">
        <Routes>
          {/* If user is logged in, /login redirects to /profile. Otherwise, show Login page. */}
          <Route path="/login" element={isLoggedIn ? <Navigate to="/profile" /> : <Login />} />

          {/* Redirect root path to the appropriate page */}
          <Route path="/" element={<Navigate to={isLoggedIn ? "/profile" : "/login"} />} />

          {/* Protected Routes are nested inside the ProtectedRoute component */}
          <Route element={<ProtectedRoute />}>
            <Route path="/profile" element={<Profile />} />
            <Route path="/meetings" element={<Meetings />} />
          </Route>

          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;