import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import formStyles from './Form.module.css';
import Spinner from './Spinner';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Clear previous errors
    setIsLoading(true);
    try {
      await login(username, password);
      // On success, redirect to the profile page
      navigate('/profile', { replace: true });

    } catch (error) {
      console.error('Login failed:', error);
      // Use a more specific error message from the backend if available
      setError(error.response?.data?.detail || 'Login failed. Please check your username and password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={formStyles.loginContainer}>
      <form onSubmit={handleSubmit} className={formStyles.loginForm}>
        <h2>Login</h2>
        <div className={formStyles.inputGroup}>
          <label htmlFor="login-username">Username</label>
          <input id="login-username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className={formStyles.inputGroup}>
          <label htmlFor="login-password">Password</label>
          <input id="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <p className={`${formStyles.formMessage} ${formStyles.error}`}>{error}</p>}
        <button type="submit" disabled={isLoading} className={formStyles.loginButton}>
          {isLoading ? <Spinner /> : 'Login'}
        </button>
      </form>
    </div>
  );
};

export default Login;