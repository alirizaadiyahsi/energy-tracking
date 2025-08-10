import authApi from './authApi';
import { LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, User, AuthServiceLoginResponse, AuthServiceRegisterResponse } from '../types';

class AuthService {
  public storeTokens(accessToken: string, refreshToken: string, rememberMe: boolean = false): void {
    if (rememberMe) {
      // For remember me, store in localStorage for persistence across browser sessions
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      localStorage.setItem('rememberMe', 'true');
      // Clear any sessionStorage tokens
      sessionStorage.removeItem('accessToken');
      sessionStorage.removeItem('refreshToken');
    } else {
      // For regular login, store in sessionStorage (expires when browser is closed)
      sessionStorage.setItem('accessToken', accessToken);
      sessionStorage.setItem('refreshToken', refreshToken);
      localStorage.removeItem('rememberMe');
      // Clear any localStorage tokens  
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  }

  public getStoredToken(tokenType: 'accessToken' | 'refreshToken'): string | null {
    // Check localStorage first (remember me tokens)
    const localToken = localStorage.getItem(tokenType);
    if (localToken) {
      return localToken;
    }
    
    // Then check sessionStorage (regular session tokens)
    return sessionStorage.getItem(tokenType);
  }

  public clearTokens(): void {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('rememberMe');
    sessionStorage.removeItem('accessToken');
    sessionStorage.removeItem('refreshToken');
  }

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await authApi.post<AuthServiceLoginResponse>('/api/v1/auth/login', credentials);
    
    // Auth service returns direct response, not wrapped in ApiResponse
    if (response.data && response.data.access_token) {
      const { access_token, refresh_token } = response.data;
      
      // Store tokens based on remember me preference
      this.storeTokens(access_token, refresh_token, credentials.remember_me || false);
      
      // Get user details from /api/v1/auth/me endpoint
      try {
        const userResponse = await authApi.get<any>('/api/v1/auth/me');
        const userData = userResponse.data;
        
        // Transform the response to match our expected format
        return {
          user: {
            id: userData.id,
            email: userData.email,
            firstName: userData.full_name ? userData.full_name.split(' ')[0] : '',
            lastName: userData.full_name ? userData.full_name.split(' ').slice(1).join(' ') : '',
            role: userData.is_superuser ? 'admin' : 'user',
            permissions: [],
            isActive: userData.is_active,
            createdAt: userData.created_at,
          },
          accessToken: access_token,
          refreshToken: refresh_token,
        };
      } catch (userError) {
        // If getting user fails, still return login success but with minimal user data
        return {
          user: {
            id: response.data.user_id,
            email: response.data.email,
            firstName: '',
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
    }
    
    throw new Error('Login failed');
  }

  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    const response = await authApi.post<AuthServiceRegisterResponse>('/api/v1/auth/register', userData);
    
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
      await authApi.post('/api/v1/auth/logout');
    } finally {
      this.clearTokens();
    }
  }

  async getCurrentUser(): Promise<User> {
    const response = await authApi.get<any>('/api/v1/auth/me');
    if (response.data) {
      const userData = response.data;
      return {
        id: userData.id,
        email: userData.email,
        firstName: userData.full_name ? userData.full_name.split(' ')[0] : '',
        lastName: userData.full_name ? userData.full_name.split(' ').slice(1).join(' ') : '',
        role: userData.is_superuser ? 'admin' : 'user',
        permissions: [],
        isActive: userData.is_active,
        createdAt: userData.created_at,
      };
    }
    throw new Error('Failed to get user info');
  }

  async refreshToken(): Promise<string> {
    const refreshToken = this.getStoredToken('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await authApi.post<{ access_token: string }>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });

    if (response.data && response.data.access_token) {
      const { access_token } = response.data;
      // Store the new access token in the same location as the refresh token
      const isRememberMe = localStorage.getItem('rememberMe') === 'true';
      if (isRememberMe) {
        localStorage.setItem('accessToken', access_token);
      } else {
        sessionStorage.setItem('accessToken', access_token);
      }
      return access_token;
    }

    throw new Error('Token refresh failed');
  }

  isAuthenticated(): boolean {
    return !!this.getStoredToken('accessToken');
  }
}

export default new AuthService();
