import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Plus, Cpu, Wifi, WifiOff, AlertTriangle, Edit, Trash2, Eye } from 'lucide-react';
import deviceService from '../services/deviceService';
import { Device, DeviceCreate, DeviceUpdate } from '../types';
import { getStatusBadgeColor } from '../utils';
import DeviceForm from '../components/DeviceForm';
import DeleteDeviceModal from '../components/DeleteDeviceModal';

const Devices: React.FC = () => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [isFormLoading, setIsFormLoading] = useState(false);
  
  const queryClient = useQueryClient();
  
  const { data: devices, isLoading, error } = useQuery(
    'devices',
    () => deviceService.getDevices()
  );

  // Create device mutation
  const createDeviceMutation = useMutation(
    (deviceData: DeviceCreate) => deviceService.createDevice(deviceData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('devices');
      },
    }
  );

  // Update device mutation
  const updateDeviceMutation = useMutation(
    ({ id, data }: { id: string; data: DeviceUpdate }) => 
      deviceService.updateDevice(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('devices');
      },
    }
  );

  // Delete device mutation
  const deleteDeviceMutation = useMutation(
    (deviceId: string) => deviceService.deleteDevice(deviceId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('devices');
      },
    }
  );

  const handleAddDevice = () => {
    setSelectedDevice(null);
    setIsFormOpen(true);
  };

  const handleEditDevice = (device: Device) => {
    setSelectedDevice(device);
    setIsFormOpen(true);
  };

  const handleDeleteDevice = (device: Device) => {
    setSelectedDevice(device);
    setIsDeleteModalOpen(true);
  };

  const handleFormSubmit = async (data: DeviceCreate | DeviceUpdate) => {
    setIsFormLoading(true);
    try {
      if (selectedDevice) {
        // Update existing device
        await updateDeviceMutation.mutateAsync({ 
          id: selectedDevice.id, 
          data: data as DeviceUpdate 
        });
      } else {
        // Create new device
        await createDeviceMutation.mutateAsync(data as DeviceCreate);
      }
      setIsFormOpen(false);
    } catch (error) {
      console.error('Error saving device:', error);
    } finally {
      setIsFormLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (selectedDevice) {
      await deleteDeviceMutation.mutateAsync(selectedDevice.id);
      setIsDeleteModalOpen(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 p-8">
        <p>Failed to load devices</p>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <Wifi className="h-4 w-4" />;
      case 'offline':
        return <WifiOff className="h-4 w-4" />;
      case 'error':
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <Cpu className="h-4 w-4" />;
    }
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-secondary-900">Devices</h1>
          <p className="mt-2 text-sm text-secondary-700">
            Manage your energy monitoring devices
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={handleAddDevice}
            className="btn btn-primary"
          >
            <Plus className="h-4 w-4" />
            Add Device
          </button>
        </div>
      </div>

      <div className="mt-8 flow-root">
        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-secondary-300">
                <thead className="bg-secondary-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wide">
                      Device
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wide">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wide">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wide">
                      Location
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-secondary-500 uppercase tracking-wide">
                      Last Seen
                    </th>
                    <th className="relative px-6 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-secondary-200">
                  {devices?.map((device) => (
                    <tr key={device.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <Cpu className="h-5 w-5 text-secondary-400 mr-3" />
                          <div>
                            <div className="text-sm font-medium text-secondary-900">
                              {device.name}
                            </div>
                            <div className="text-sm text-secondary-500">
                              {device.id}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {device.type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(device.status)}`}>
                          {getStatusIcon(device.status)}
                          <span className="ml-1">{device.status}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {device.location || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-secondary-500">
                        {device.last_seen ? new Date(device.last_seen).toLocaleString() : 'Never'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end space-x-2">
                          <button 
                            onClick={() => handleEditDevice(device)}
                            className="text-primary-600 hover:text-primary-900 p-1"
                            title="Edit device"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button 
                            onClick={() => handleDeleteDevice(device)}
                            className="text-red-600 hover:text-red-900 p-1"
                            title="Delete device"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {(!devices || devices.length === 0) && (
        <div className="text-center py-12">
          <Cpu className="mx-auto h-12 w-12 text-secondary-400" />
          <h3 className="mt-2 text-sm font-medium text-secondary-900">No devices</h3>
          <p className="mt-1 text-sm text-secondary-500">
            Get started by adding your first device.
          </p>
          <div className="mt-6">
            <button
              type="button"
              onClick={handleAddDevice}
              className="btn btn-primary"
            >
              <Plus className="h-4 w-4" />
              Add Device
            </button>
          </div>
        </div>
      )}

      {/* Device Form Modal */}
      <DeviceForm
        device={selectedDevice}
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        isLoading={isFormLoading}
      />

      {/* Delete Confirmation Modal */}
      <DeleteDeviceModal
        device={selectedDevice}
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDeleteConfirm}
        isLoading={deleteDeviceMutation.isLoading}
      />
    </div>
  );
};

export default Devices;
