// useApi: generic hook for API requests with loading/error state
import { useState, useCallback } from 'react';
import { getAuthToken } from '../services/auth';
import { API_BASE_URL } from '../utils/constants';

export function useApi<T = any>(endpoint: string, options?: RequestInit) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (body?: any) => {
    setLoading(true);
    setError(null);
    try {
      const token = getAuthToken();
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          ...(options?.headers || {}),
          Authorization: token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) throw new Error('API error');
      const json = await res.json();
      setData(json);
      return json;
    } catch (e: any) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, [endpoint, options]);

  return { data, loading, error, fetchData };
}
