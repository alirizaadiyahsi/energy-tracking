import api from './api';
import { DashboardData, ApiResponse, ChartDataPoint } from '../types';

export interface ChartParams {
  interval: 'minutely' | 'hourly' | 'daily';
  timeRange: '1h' | '24h' | '7d' | '30d';
  deviceId?: string;
}

class DashboardService {
  async getDashboardData(): Promise<DashboardData> {
    const response = await api.get<ApiResponse<DashboardData>>('/api/v1/analytics/dashboard');
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch dashboard data');
  }

  async getEnergyChart(params: ChartParams): Promise<ChartDataPoint[]> {
    const queryParams = new URLSearchParams({
      interval: params.interval,
      time_range: params.timeRange,
      ...(params.deviceId && { device_id: params.deviceId })
    });
    
    const response = await api.get<ApiResponse<ChartDataPoint[]>>(
      `/api/v1/analytics/consumption/trends?${queryParams}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch energy chart data');
  }

  async getPowerChart(params: ChartParams): Promise<ChartDataPoint[]> {
    const queryParams = new URLSearchParams({
      interval: params.interval,
      time_range: params.timeRange,
      ...(params.deviceId && { device_id: params.deviceId })
    });
    
    const response = await api.get<ApiResponse<ChartDataPoint[]>>(
      `/api/v1/analytics/power/trends?${queryParams}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch power chart data');
  }
}

export default new DashboardService();
