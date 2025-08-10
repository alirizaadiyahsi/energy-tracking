import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { Device, DeviceCreate, DeviceUpdate } from '../types';

interface DeviceFormProps {
  device?: Device | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: DeviceCreate | DeviceUpdate) => Promise<void>;
  isLoading?: boolean;
}

const DEVICE_TYPES = [
  { value: 'hvac', label: 'HVAC System' },
  { value: 'lighting', label: 'Lighting' },
  { value: 'server', label: 'Server' },
  { value: 'sensor', label: 'Sensor' },
  { value: 'meter', label: 'Meter' },
  { value: 'gateway', label: 'Gateway' },
  { value: 'appliance', label: 'Appliance' },
  { value: 'industrial', label: 'Industrial Equipment' },
  { value: 'controller', label: 'Controller' }
] as const;

const DEVICE_STATUSES = [
  { value: 'online', label: 'Online' },
  { value: 'offline', label: 'Offline' },
  { value: 'error', label: 'Error' }
] as const;

const DeviceForm: React.FC<DeviceFormProps> = ({
  device,
  isOpen,
  onClose,
  onSubmit,
  isLoading = false
}) => {
  const [formData, setFormData] = useState<DeviceCreate & { status?: Device['status'] }>({
    name: '',
    type: 'sensor',
    location: '',
    description: '',
    base_power: undefined,
    base_voltage: undefined,
    firmware_version: '',
    model: '',
    metadata: {}
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Update form data when device prop changes
  useEffect(() => {
    if (device) {
      setFormData({
        name: device.name,
        type: device.type,
        location: device.location || '',
        description: device.description || '',
        status: device.status,
        base_power: device.base_power || undefined,
        base_voltage: device.base_voltage || undefined,
        firmware_version: device.firmware_version || '',
        model: device.model || '',
        metadata: device.metadata || {}
      });
    } else {
      setFormData({
        name: '',
        type: 'sensor',
        location: '',
        description: '',
        base_power: undefined,
        base_voltage: undefined,
        firmware_version: '',
        model: '',
        metadata: {}
      });
    }
    setErrors({});
  }, [device, isOpen]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Device name is required';
    }

    if (!formData.type) {
      newErrors.type = 'Device type is required';
    }

    if (formData.base_power !== undefined && formData.base_power < 0) {
      newErrors.base_power = 'Base power must be positive';
    }

    if (formData.base_voltage !== undefined && formData.base_voltage < 0) {
      newErrors.base_voltage = 'Base voltage must be positive';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      // Remove empty strings and undefined values
      const cleanedData = Object.entries(formData).reduce((acc, [key, value]) => {
        if (value !== '' && value !== undefined) {
          acc[key as keyof typeof formData] = value;
        }
        return acc;
      }, {} as any);

      await onSubmit(cleanedData);
      onClose();
    } catch (error) {
      console.error('Error submitting form:', error);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? undefined : Number(value)) : value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-25" onClick={onClose} />
        
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b">
            <h3 className="text-lg font-medium text-gray-900">
              {device ? 'Edit Device' : 'Add New Device'}
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Device Name */}
              <div className="md:col-span-2">
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Device Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 ${
                    errors.name ? 'border-red-300' : ''
                  }`}
                  placeholder="Enter device name"
                />
                {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
              </div>

              {/* Device Type */}
              <div>
                <label htmlFor="type" className="block text-sm font-medium text-gray-700">
                  Device Type *
                </label>
                <select
                  id="type"
                  name="type"
                  value={formData.type}
                  onChange={handleInputChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
                  {DEVICE_TYPES.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                {errors.type && <p className="mt-1 text-sm text-red-600">{errors.type}</p>}
              </div>

              {/* Device Status (only for edit) */}
              {device && (
                <div>
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                    Status
                  </label>
                  <select
                    id="status"
                    name="status"
                    value={formData.status}
                    onChange={handleInputChange}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                  >
                    {DEVICE_STATUSES.map(status => (
                      <option key={status.value} value={status.value}>
                        {status.label}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Location */}
              <div className={device ? '' : 'md:col-span-2'}>
                <label htmlFor="location" className="block text-sm font-medium text-gray-700">
                  Location
                </label>
                <input
                  type="text"
                  id="location"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                  placeholder="Enter device location"
                />
              </div>

              {/* Description */}
              <div className="md:col-span-2">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows={3}
                  value={formData.description}
                  onChange={handleInputChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                  placeholder="Enter device description"
                />
              </div>

              {/* Model */}
              <div>
                <label htmlFor="model" className="block text-sm font-medium text-gray-700">
                  Model
                </label>
                <input
                  type="text"
                  id="model"
                  name="model"
                  value={formData.model}
                  onChange={handleInputChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                  placeholder="Enter device model"
                />
              </div>

              {/* Firmware Version */}
              <div>
                <label htmlFor="firmware_version" className="block text-sm font-medium text-gray-700">
                  Firmware Version
                </label>
                <input
                  type="text"
                  id="firmware_version"
                  name="firmware_version"
                  value={formData.firmware_version}
                  onChange={handleInputChange}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                  placeholder="Enter firmware version"
                />
              </div>

              {/* Base Power */}
              <div>
                <label htmlFor="base_power" className="block text-sm font-medium text-gray-700">
                  Base Power (kW)
                </label>
                <input
                  type="number"
                  id="base_power"
                  name="base_power"
                  step="0.1"
                  min="0"
                  value={formData.base_power || ''}
                  onChange={handleInputChange}
                  className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 ${
                    errors.base_power ? 'border-red-300' : ''
                  }`}
                  placeholder="Enter base power"
                />
                {errors.base_power && <p className="mt-1 text-sm text-red-600">{errors.base_power}</p>}
              </div>

              {/* Base Voltage */}
              <div>
                <label htmlFor="base_voltage" className="block text-sm font-medium text-gray-700">
                  Base Voltage (V)
                </label>
                <input
                  type="number"
                  id="base_voltage"
                  name="base_voltage"
                  step="0.1"
                  min="0"
                  value={formData.base_voltage || ''}
                  onChange={handleInputChange}
                  className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 ${
                    errors.base_voltage ? 'border-red-300' : ''
                  }`}
                  placeholder="Enter base voltage"
                />
                {errors.base_voltage && <p className="mt-1 text-sm text-red-600">{errors.base_voltage}</p>}
              </div>
            </div>

            {/* Form Actions */}
            <div className="flex justify-end space-x-3 pt-6 border-t">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Saving...' : (device ? 'Update Device' : 'Create Device')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default DeviceForm;
