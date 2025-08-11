import React, { useState } from 'react';
import axios from 'axios';

const Login = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // For the initial login, we use axios directly as we don't have a token yet.
      const response = await axios.post('http://127.0.0.1:8000/api/token/', {
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

    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Login</h2>
      <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Username" required />
      <br />
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" required />
      <br />
      <button type="submit">Login</button>
    </form>
  );
};

export default Login;