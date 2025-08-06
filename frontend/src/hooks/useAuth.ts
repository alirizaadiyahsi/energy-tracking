// useAuth: React hook for authentication state and actions
import { useState, useEffect, useCallback } from 'react';
import { login, logout, getCurrentUser, fetchProfile } from '../services/auth';

export function useAuth() {
  const [user, setUser] = useState<any>(getCurrentUser());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await login(email, password);
      setUser(data.user);
      return data;
    } catch (e: any) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const handleLogout = useCallback(() => {
    logout();
    setUser(null);
  }, []);

  const refreshProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const profile = await fetchProfile();
      setUser(profile);
      return profile;
    } catch (e: any) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setUser(getCurrentUser());
  }, []);

  return { user, loading, error, login: handleLogin, logout: handleLogout, refreshProfile };
}
