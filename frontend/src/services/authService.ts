import authApi from './authApi';
import { LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, User, AuthServiceLoginResponse, AuthServiceRegisterResponse } from '../types';

class AuthService {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await authApi.post<AuthServiceLoginResponse>('/auth/login', credentials);
    
    // Auth service returns direct response, not wrapped in ApiResponse
    if (response.data && response.data.access_token) {
      const { access_token, refresh_token } = response.data;
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      
      // Transform the response to match our expected format
      return {
        user: {
          id: response.data.user_id,
          email: response.data.email,
          firstName: '', // Will be filled from /auth/me
          lastName: '',
          role: '',
          permissions: [],
          isActive: true,
          createdAt: new Date().toISOString(),
        },
        accessToken: access_token,
        refreshToken: refresh_token,
      };
    }
    
    throw new Error('Login failed');
  }

  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    const response = await authApi.post<AuthServiceRegisterResponse>('/auth/register', userData);
    
    // For register, we need to login after registration to get tokens
    if (response.data && response.data.user_id) {
      // After successful registration, login to get tokens
      return await this.login({
        email: userData.email,
        password: userData.password,
      });
    }
    
    throw new Error('Registration failed');
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
    const response = await authApi.get<User>('/auth/me');
    if (response.data) {
      return response.data;
    }
    throw new Error('Failed to get user info');
  }

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await authApi.post<{ access_token: string }>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    if (response.data && response.data.access_token) {
      const { access_token } = response.data;
      localStorage.setItem('accessToken', access_token);
      return access_token;
    }

    throw new Error('Token refresh failed');
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('accessToken');
  }
}

export default new AuthService();
