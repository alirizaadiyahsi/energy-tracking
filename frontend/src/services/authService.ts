import authApi from './authApi';
import { LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, User, ApiResponse } from '../types';

class AuthService {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await authApi.post<ApiResponse<LoginResponse>>('/auth/login', credentials);
    
    if (response.data.success && response.data.data) {
      const { accessToken, refreshToken } = response.data.data;
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      return response.data.data;
    }
    
    throw new Error(response.data.message || 'Login failed');
  }

  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    const response = await authApi.post<ApiResponse<RegisterResponse>>('/auth/register', userData);
    
    if (response.data.success && response.data.data) {
      const { accessToken, refreshToken } = response.data.data;
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      return response.data.data;
    }
    
    throw new Error(response.data.message || 'Registration failed');
  }

  async logout(): Promise<void> {
    try {
      await authApi.post('/auth/logout');
    } finally {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await authApi.get<ApiResponse<User>>('/auth/me');
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to get user info');
  }

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await authApi.post<ApiResponse<{ accessToken: string }>>('/auth/refresh', {
      refreshToken,
    });

    if (response.data.success && response.data.data) {
      const { accessToken } = response.data.data;
      localStorage.setItem('accessToken', accessToken);
      return accessToken;
    }

    throw new Error(response.data.message || 'Token refresh failed');
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('accessToken');
  }
}

export default new AuthService();
