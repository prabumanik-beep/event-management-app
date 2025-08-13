import axios from 'axios';

export const baseURL = process.env.REACT_APP_API_URL || 'https://event-management-app-ejk0.onrender.com/api/';

const api = axios.create({
  baseURL: baseURL,
});

// Request Interceptor: Add the access token to every outgoing request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor: Handle expired access tokens by refreshing them
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${baseURL}token/refresh/`, { refresh: refreshToken });
        localStorage.setItem('access_token', response.data.access);
        return api(originalRequest); // Retry the original request with the new token
      } catch (refreshError) {
        // If refresh fails, redirect to login (handled by AuthContext)
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default api;