import React, { useState } from 'react';
import axios from 'axios';
import { baseURL } from '../api';
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
      // For the initial login, we use axios directly as we don't have a token yet.
      const response = await axios.post(`${baseURL}token/`, {
        username,
        password,
      });
      
      // Store tokens in localStorage
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);

      console.log('Login successful!');
      // Update the global auth state
      login();
      // Redirect to the profile page after successful login
      navigate('/profile');

    } catch (error) {
      console.error('Login failed:', error);
      // Use a more specific error message from the backend if available
      setError(error.response?.data?.detail || 'Login failed. Please check your username and password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      <div>
        <label htmlFor="login-username">Username</label>
        <input id="login-username" type="text" value={username} onChange={(e) => setUsername(e.target.value)} required />
      </div>
      <div>
        <label htmlFor="login-password">Password</label>
        <input id="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </div>
      {error && <p className={`${formStyles.formMessage} ${formStyles.error}`}>{error}</p>}
      <button type="submit" disabled={isLoading} className={formStyles.loginButton}>
        {isLoading ? <Spinner /> : 'Login'}
      </button>
    </form>
  );
};

export default Login;