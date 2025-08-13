import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import styles from './Navbar.module.css';

const Navbar = () => {
  const { isLoggedIn, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className={styles.navbar}>
      <div className={styles.navBrand}>
        <Link to="/">EventApp</Link>
      </div>
      <div className={styles.navLinks}>
        {isLoggedIn ? (
          <>
            <Link to="/profile" className={styles.navLink}>Profile</Link>
            <Link to="/meetings" className={styles.navLink}>My Meetings</Link>
            <button onClick={handleLogout} className={styles.logoutButton}>Logout</button>
          </>
        ) : (
          <Link to="/login" className={styles.navLink}>Login</Link>
        )}
      </div>
    </nav>
  );
};

export default Navbar;