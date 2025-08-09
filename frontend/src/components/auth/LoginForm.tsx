import React, { useState } from 'react';
import Input from '../common/Input';
import Button from '../common/Button';

interface LoginFormProps {
  onLogin?: (email: string, password: string) => void;
  loading?: boolean;
  error?: string;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLogin, loading, error }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onLogin) onLogin(email, password);
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-sm mx-auto p-6 bg-white rounded shadow">
      <h2 className="text-xl font-bold mb-4">Login</h2>
      <Input
        label="Email"
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        required
      />
      <Input
        label="Password"
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
      />
      {error && <div className="text-red-500 text-sm mb-2">{error}</div>}
      <Button type="submit" disabled={loading} className="w-full mt-2">
        {loading ? 'Logging in...' : 'Login'}
      </Button>
    </form>
  );
};

export default LoginForm;
