import axios, { AxiosInstance } from 'axios';

// Utility function to get access token from either storage location
const getAccessToken = (): string | null => {
  // Check localStorage first (remember me tokens)
  const localToken = localStorage.getItem('accessToken');
  if (localToken) {
    return localToken;
  }
  
  // Then check sessionStorage (regular session tokens)
  return sessionStorage.getItem('accessToken');
};

// Create dedicated auth API instance
const authApi: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token for protected endpoints
authApi.interceptors.request.use(
  (config) => {
    // Add token for protected endpoints like /auth/me, /auth/logout
    if (config.url?.includes('/me') || config.url?.includes('/logout')) {
      const token = getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for auth API
authApi.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || error.message || 'An error occurred';
    
    // Don't show toast for auth errors, let the component handle them
    console.error('Auth API Error:', message);
    
    return Promise.reject(error);
  }
);

export default authApi;
