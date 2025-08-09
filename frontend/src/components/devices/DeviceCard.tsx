import React from 'react';

type DeviceCardProps = {
  name: string;
  status: string;
  lastSeen: string;
  onClick?: () => void;
};

const DeviceCard: React.FC<DeviceCardProps> = ({ name, status, lastSeen, onClick }) => (
  <div className="bg-white rounded shadow p-4 cursor-pointer hover:bg-blue-50" onClick={onClick}>
    <div className="font-bold text-lg">{name}</div>
    <div className="text-sm text-gray-500">Status: {status}</div>
    <div className="text-xs text-gray-400">Last seen: {lastSeen}</div>
  </div>
);

export default DeviceCard;
