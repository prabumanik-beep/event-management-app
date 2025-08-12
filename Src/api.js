import axios from 'axios';

export const baseURL = process.env.NODE_ENV === 'production'
  ? '/api/'
  : 'http://127.0.0.1:8000/api/';

const api = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Use an interceptor to add the auth token to every request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = 'Bearer ' + token;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// This interceptor handles automatic token refreshing
api.interceptors.response.use(
  (res) => {
    return res;
  },
  async (err) => {
    const originalConfig = err.config;

    // If the error is 401 and it's not a retry, try to refresh the token
    if (originalConfig.url !== '/token/refresh/' && err.response) {
      if (err.response.status === 401 && !originalConfig._retry) {
        originalConfig._retry = true;

        try {
          const refreshToken = localStorage.getItem('refresh_token');
          const rs = await axios.post(baseURL + 'token/refresh/', {
            refresh: refreshToken,
          });

          const { access } = rs.data;
          localStorage.setItem('access_token', access);

          return api(originalConfig);
        } catch (_error) {
          // Handle failed refresh by cleaning up and redirecting to login.
          console.error("Session expired. Please log in again.");
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login'; // Force a redirect to the login page.
          return Promise.reject(_error);
        }
      }
    }
    return Promise.reject(err);
  }
);

export default api;