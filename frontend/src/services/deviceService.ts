import api from './api';
import { Device, EnergyReading, DashboardData, ApiResponse, PaginatedResponse } from '../types';

class DeviceService {
  async getDevices(): Promise<Device[]> {
    const response = await api.get<ApiResponse<Device[]>>('/devices');
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch devices');
  }

  async getDevice(id: string): Promise<Device> {
    const response = await api.get<ApiResponse<Device>>(`/devices/${id}`);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch device');
  }

  async getDeviceReadings(
    deviceId: string, 
    limit: number = 100,
    from?: string,
    to?: string
  ): Promise<EnergyReading[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });
    
    if (from) params.append('from', from);
    if (to) params.append('to', to);

    const response = await api.get<ApiResponse<EnergyReading[]>>(
      `/devices/${deviceId}/readings?${params.toString()}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch device readings');
  }

  async createDevice(deviceData: Partial<Device>): Promise<Device> {
    const response = await api.post<ApiResponse<Device>>('/devices', deviceData);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to create device');
  }

  async updateDevice(id: string, deviceData: Partial<Device>): Promise<Device> {
    const response = await api.put<ApiResponse<Device>>(`/devices/${id}`, deviceData);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to update device');
  }

  async deleteDevice(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<null>>(`/devices/${id}`);
    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to delete device');
    }
  }
}

export default new DeviceService();
