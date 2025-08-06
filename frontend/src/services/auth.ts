// Auth service for login, logout, and session management
import { API_BASE_URL, AUTH_TOKEN_KEY, SESSION_STORAGE_KEY } from '../utils/constants';

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error('Invalid credentials');
  const data = await res.json();
  localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(data.user));
  return data;
}

export function logout() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

export function getCurrentUser() {
  const user = localStorage.getItem(SESSION_STORAGE_KEY);
  return user ? JSON.parse(user) : null;
}

export function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export async function fetchProfile() {
  const token = getAuthToken();
  if (!token) throw new Error('No auth token');
  const res = await fetch(`${API_BASE_URL}/auth/profile`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error('Failed to fetch profile');
  return res.json();
}
