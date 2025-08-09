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
  remember_me?: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface LoginResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface RegisterResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

// Auth service response interfaces (match backend format)
export interface AuthServiceLoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  email: string;
  session_id: string;
}

export interface AuthServiceRegisterResponse {
  message: string;
  user_id: string;
  email: string;
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

// Processing types (for data-processing service)
export interface ProcessingJob {
  id: number;
  jobType: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  parameters?: Record<string, any>;
  result?: Record<string, any>;
  errorMessage?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  createdBy?: string;
}

export interface AnomalyResult {
  isAnomaly: boolean;
  score: number;
  threshold: number;
  message?: string;
}

// Analytics types
export interface EnergyMetrics {
  id: number;
  deviceId: string;
  metricType: string;
  periodStart: string;
  periodEnd: string;
  totalEnergy: number;
  avgPower: number;
  maxPower: number;
  minPower: number;
  energyCost: number;
  efficiencyScore?: number;
  anomalyDetected: boolean;
  anomalyScore?: number;
  dataPointsCount: number;
  createdAt: string;
  updatedAt?: string;
}

export interface AnalyticsData {
  totalConsumption: number;
  avgDailyConsumption: number;
  peakDemand: number;
  efficiencyScore: number;
  costSavings: number;
  anomaliesDetected: number;
}

export interface ConsumptionTrend {
  date: string;
  consumption: number;
  cost?: number;
  deviceId?: string;
}

export interface EfficiencyReport {
  deviceId: string;
  deviceName: string;
  currentEfficiency: number;
  targetEfficiency: number;
  improvementPotential: number;
  recommendations: string[];
}

// Notification types
export interface Notification {
  id: string;
  recipient: string;
  subject: string;
  message: string;
  type: string;
  status: 'pending' | 'sent' | 'failed';
  createdAt: string;
  sentAt?: string;
}

export interface NotificationTemplate {
  id: string;
  name: string;
  description: string;
  subject: string;
  body: string;
}

export interface NotificationRequest {
  recipient: string;
  subject: string;
  message: string;
  type?: string;
  templateId?: string;
  templateData?: Record<string, any>;
}

export interface AlertRequest {
  recipients: string[];
  subject: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  deviceId?: string;
}

// Form validation types
export interface FormErrors {
  [key: string]: string | string[] | undefined;
}

// Utility types
export type Status = 'idle' | 'loading' | 'success' | 'error';

export interface LoadingState {
  [key: string]: boolean;
}

export interface ErrorState {
  [key: string]: string | null;
}

// Component prop types
export interface TableColumn {
  key: string;
  title: string;
  sortable?: boolean;
  render?: (value: any, record: any) => any;
}

export interface FilterOption {
  label: string;
  value: string | number;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface RealTimeUpdate {
  deviceId: string;
  data: EnergyReading;
  timestamp: string;
}
