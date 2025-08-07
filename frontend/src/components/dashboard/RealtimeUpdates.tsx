import React, { useEffect, useState } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

const RealtimeUpdates: React.FC = () => {
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onmessage = (event) => {
      setMessage(event.data);
    };
    return () => ws.close();
  }, []);

  return (
    <div className="bg-white rounded shadow p-4 mt-4">
      <h3 className="font-semibold mb-2">Realtime Updates</h3>
      <div className="text-gray-700">{message || 'Waiting for updates...'}</div>
    </div>
  );
};

export default RealtimeUpdates;
