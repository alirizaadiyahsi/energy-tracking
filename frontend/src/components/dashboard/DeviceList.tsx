import React from 'react';

type Device = {
  id: string;
  name: string;
  status: string;
  lastSeen: string;
};

type DeviceListProps = {
  devices: Device[];
  onSelect?: (id: string) => void;
};

const DeviceList: React.FC<DeviceListProps> = ({ devices, onSelect }) => (
  <table className="min-w-full bg-white rounded shadow">
    <thead>
      <tr>
        <th className="py-2 px-4">Name</th>
        <th className="py-2 px-4">Status</th>
        <th className="py-2 px-4">Last Seen</th>
        <th className="py-2 px-4">Actions</th>
      </tr>
    </thead>
    <tbody>
      {devices.map(device => (
        <tr key={device.id} className="border-t">
          <td className="py-2 px-4">{device.name}</td>
          <td className="py-2 px-4">{device.status}</td>
          <td className="py-2 px-4">{device.lastSeen}</td>
          <td className="py-2 px-4">
            <button
              className="text-blue-600 hover:underline"
              onClick={() => onSelect && onSelect(device.id)}
            >
              Details
            </button>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
);

export default DeviceList;
