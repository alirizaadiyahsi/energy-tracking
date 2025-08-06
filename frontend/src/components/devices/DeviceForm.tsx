import React, { useState } from 'react';
import Input from '../common/Input';
import Button from '../common/Button';

type DeviceFormProps = {
  initial?: { name: string; status: string };
  onSubmit: (data: { name: string; status: string }) => void;
  loading?: boolean;
};

const DeviceForm: React.FC<DeviceFormProps> = ({ initial, onSubmit, loading }) => {
  const [name, setName] = useState(initial?.name || '');
  const [status, setStatus] = useState(initial?.status || 'active');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name, status });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input label="Device Name" value={name} onChange={e => setName(e.target.value)} required />
      <Input label="Status" value={status} onChange={e => setStatus(e.target.value)} required />
      <Button type="submit" disabled={loading}>{loading ? 'Saving...' : 'Save Device'}</Button>
    </form>
  );
};

export default DeviceForm;
