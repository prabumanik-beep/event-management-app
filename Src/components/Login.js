import React, { useState } from 'react';
import axios from 'axios';
import { baseURL } from '../api'; // Import the base URL
import { useNavigate } from 'react-router-dom';
import '../styles/Form.css';

const Login = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

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
      // Notify the parent component that login was successful
      if (onLoginSuccess) {
        onLoginSuccess();
      }
      // Redirect to the profile page after successful login
      navigate('/profile');

    } catch (error) {
      console.error('Login failed:', error);
      setError('Login failed. Please check your username and password.');
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
      {error && <p className="form-message error">{error}</p>}
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};

export default Login;