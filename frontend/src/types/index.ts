export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  permissions: string[];
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface Device {
  id: string;
  name: string;
  type: 'sensor' | 'meter' | 'gateway';
  status: 'online' | 'offline' | 'error';
  location?: string;
  lastSeen?: string;
  batteryLevel?: number;
  firmwareVersion?: string;
  metadata: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface EnergyReading {
  id: string;
  deviceId: string;
  timestamp: string;
  power: number;
  voltage: number;
  current: number;
  frequency: number;
  powerFactor: number;
  energy: number;
  metadata: Record<string, any>;
}

export interface Alert {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'error' | 'success';
  deviceId?: string;
  isRead: boolean;
  createdAt: string;
}

export interface DashboardData {
  totalDevices: number;
  onlineDevices: number;
  totalEnergyToday: number;
  totalEnergyMonth: number;
  averagePower: number;
  alerts: Alert[];
  recentReadings: EnergyReading[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  totalPages: number;
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}
