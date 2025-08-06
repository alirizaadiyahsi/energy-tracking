// Application-wide constants for the energy tracking app

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws';

export const ENERGY_UNITS = ['kWh', 'Wh'] as const;
export const SUPPORTED_LANGUAGES = ['en', 'tr'] as const;

export const SESSION_STORAGE_KEY = 'energy-tracking-session';
export const AUTH_TOKEN_KEY = 'energy-tracking-auth-token';

export const DEVICE_STATUS = {
  ONLINE: 'online',
  OFFLINE: 'offline',
  ERROR: 'error',
} as const;

export const ROLES = ['admin', 'manager', 'user'] as const;

// Vite's import.meta.env typing workaround
declare global {
  interface ImportMeta {
    env: {
      VITE_API_BASE_URL?: string;
      VITE_WS_BASE_URL?: string;
      [key: string]: string | undefined;
    };
  }
}
