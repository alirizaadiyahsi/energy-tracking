import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Device } from '../types';

interface DeleteDeviceModalProps {
  device: Device | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isLoading?: boolean;
}

const DeleteDeviceModal: React.FC<DeleteDeviceModalProps> = ({
  device,
  isOpen,
  onClose,
  onConfirm,
  isLoading = false
}) => {
  if (!isOpen || !device) return null;

  const handleConfirm = async () => {
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      console.error('Error deleting device:', error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-25" onClick={onClose} />
        
        <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
          <div className="flex items-center justify-between p-6 border-b">
            <h3 className="text-lg font-medium text-gray-900">
              Delete Device
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="p-6">
            <div className="flex items-center mb-4">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-10 w-10 text-red-500" />
              </div>
              <div className="ml-4">
                <h4 className="text-lg font-medium text-gray-900">
                  Are you sure?
                </h4>
                <p className="text-sm text-gray-500 mt-1">
                  This action cannot be undone.
                </p>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-gray-700">
                You are about to delete the device:
              </p>
              <div className="mt-2">
                <p className="font-medium text-gray-900">{device.name}</p>
                <p className="text-sm text-gray-500">
                  Type: {device.type} • Location: {device.location || 'Not specified'}
                </p>
                <p className="text-sm text-gray-500">ID: {device.id}</p>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <AlertTriangle className="h-5 w-5 text-yellow-400 mt-0.5" />
                <div className="ml-3">
                  <h5 className="text-sm font-medium text-yellow-800">
                    Warning
                  </h5>
                  <p className="text-sm text-yellow-700 mt-1">
                    Deleting this device will also remove all associated energy readings and historical data.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={isLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Deleting...' : 'Delete Device'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteDeviceModal;
