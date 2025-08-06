import api from './api';
import { DashboardData, ApiResponse, ChartDataPoint } from '../types';

class DashboardService {
  async getDashboardData(): Promise<DashboardData> {
    const response = await api.get<ApiResponse<DashboardData>>('/dashboard');
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch dashboard data');
  }

  async getEnergyChart(period: 'day' | 'week' | 'month' | 'year' = 'day'): Promise<ChartDataPoint[]> {
    const response = await api.get<ApiResponse<ChartDataPoint[]>>(`/dashboard/energy-chart?period=${period}`);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch energy chart data');
  }

  async getPowerChart(period: 'day' | 'week' | 'month' | 'year' = 'day'): Promise<ChartDataPoint[]> {
    const response = await api.get<ApiResponse<ChartDataPoint[]>>(`/dashboard/power-chart?period=${period}`);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch power chart data');
  }
}

export default new DashboardService();
