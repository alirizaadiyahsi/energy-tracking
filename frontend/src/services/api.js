import axios from 'axios';

// API Base URLs from environment
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const AUTH_BASE_URL = process.env.REACT_APP_AUTH_URL || 'http://localhost:8005';

// Create axios instances
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const authClient = axios.create({
  baseURL: `${AUTH_BASE_URL}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
const addAuthInterceptor = (client) => {
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );
};

// Response interceptor for token refresh
const addRefreshInterceptor = (client) => {
  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = localStorage.getItem('refreshToken');
          if (!refreshToken) {
            throw new Error('No refresh token');
          }

          const response = await authClient.post('/auth/refresh', {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data;
          localStorage.setItem('accessToken', access_token);
          
          if (refresh_token) {
            localStorage.setItem('refreshToken', refresh_token);
          }

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return client(originalRequest);
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );
};

// Apply interceptors
addAuthInterceptor(apiClient);
addAuthInterceptor(authClient);
addRefreshInterceptor(apiClient);
addRefreshInterceptor(authClient);

// Authentication API
export const authAPI = {
  login: async (email, password) => {
    const response = await authClient.post('/auth/login', { email, password });
    return response.data;
  },

  register: async (userData) => {
    const response = await authClient.post('/auth/register', userData);
    return response.data;
  },

  logout: async () => {
    const response = await authClient.post('/auth/logout');
    return response.data;
  },

  refreshToken: async (refreshToken) => {
    const response = await authClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  getProfile: async () => {
    const response = await authClient.get('/auth/me');
    return response.data;
  },

  updateProfile: async (profileData) => {
    const response = await authClient.put('/users/profile', profileData);
    return response.data;
  },

  changePassword: async (oldPassword, newPassword) => {
    const response = await authClient.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
    return response.data;
  },

  requestPasswordReset: async (email) => {
    const response = await authClient.post('/auth/password-reset-request', { email });
    return response.data;
  },

  resetPassword: async (token, newPassword) => {
    const response = await authClient.post('/auth/password-reset', {
      token,
      new_password: newPassword,
    });
    return response.data;
  },

  verifyEmail: async (token) => {
    const response = await authClient.post('/auth/verify-email', { token });
    return response.data;
  },
};

// Data API
export const dataAPI = {
  getDevices: async () => {
    const response = await apiClient.get('/data/devices');
    return response.data;
  },

  getDevice: async (deviceId) => {
    const response = await apiClient.get(`/data/devices/${deviceId}`);
    return response.data;
  },

  updateDevice: async (deviceId, deviceData) => {
    const response = await apiClient.put(`/data/devices/${deviceId}`, deviceData);
    return response.data;
  },

  deleteDevice: async (deviceId) => {
    const response = await apiClient.delete(`/data/devices/${deviceId}`);
    return response.data;
  },

  getDeviceData: async (deviceId, startTime, endTime) => {
    const response = await apiClient.get(`/data/devices/${deviceId}/data`, {
      params: { start_time: startTime, end_time: endTime },
    });
    return response.data;
  },

  ingestData: async (dataPoints) => {
    const response = await apiClient.post('/data/ingest/batch', dataPoints);
    return response.data;
  },
};

// Analytics API
export const analyticsAPI = {
  getDashboardStats: async () => {
    const response = await apiClient.get('/analytics/dashboard');
    return response.data;
  },

  getEnergyConsumption: async (timeRange) => {
    const response = await apiClient.get('/analytics/consumption', {
      params: timeRange,
    });
    return response.data;
  },

  getUsagePatterns: async (deviceId, period) => {
    const response = await apiClient.get('/analytics/patterns', {
      params: { device_id: deviceId, period },
    });
    return response.data;
  },

  getCostAnalysis: async (timeRange) => {
    const response = await apiClient.get('/analytics/costs', {
      params: timeRange,
    });
    return response.data;
  },

  getEfficiencyMetrics: async () => {
    const response = await apiClient.get('/analytics/efficiency');
    return response.data;
  },

  generateReport: async (reportConfig) => {
    const response = await apiClient.post('/analytics/reports', reportConfig);
    return response.data;
  },
};

// Notification API
export const notificationAPI = {
  getNotifications: async () => {
    const response = await apiClient.get('/notifications');
    return response.data;
  },

  markAsRead: async (notificationId) => {
    const response = await apiClient.put(`/notifications/${notificationId}/read`);
    return response.data;
  },

  getSettings: async () => {
    const response = await apiClient.get('/notifications/settings');
    return response.data;
  },

  updateSettings: async (settings) => {
    const response = await apiClient.put('/notifications/settings', settings);
    return response.data;
  },
};

// System API
export const systemAPI = {
  getHealth: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  getServices: async () => {
    const response = await apiClient.get('/services');
    return response.data;
  },

  getMetrics: async () => {
    const response = await apiClient.get('/metrics');
    return response.data;
  },
};

export { apiClient, authClient };
