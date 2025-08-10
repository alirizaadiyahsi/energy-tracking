import api from './api';
import { Device, DeviceCreate, DeviceUpdate, EnergyReading, ApiResponse } from '../types';

class DeviceService {
  async getDevices(): Promise<Device[]> {
    // Use the MQTT data-ingestion endpoint with real-time device data
    const response = await api.get<ApiResponse<Device[]>>('/api/v1/data-ingestion/devices');
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch devices');
  }

  async getDevice(id: string): Promise<Device> {
    // Use the new data-ingestion endpoint
    const response = await api.get<ApiResponse<Device>>(`/api/v1/data-ingestion/devices/${id}/db`);
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
      `/api/v1/data-ingestion/devices/${deviceId}/readings?${params.toString()}`
    );
    
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch device readings');
  }

  async createDevice(deviceData: DeviceCreate): Promise<Device> {
    const response = await api.post<ApiResponse<Device>>('/api/v1/data-ingestion/devices', deviceData);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to create device');
  }

  async updateDevice(id: string, deviceData: DeviceUpdate): Promise<Device> {
    const response = await api.put<ApiResponse<Device>>(`/api/v1/data-ingestion/devices/${id}`, deviceData);
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to update device');
  }

  async deleteDevice(id: string): Promise<void> {
    const response = await api.delete<ApiResponse<null>>(`/api/v1/data-ingestion/devices/${id}`);
    if (!response.data.success) {
      throw new Error(response.data.message || 'Failed to delete device');
    }
  }
}

export default new DeviceService();
