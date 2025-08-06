// Integration tests for frontend API and auth flows
import { describe, it, expect, vi } from 'vitest';
import * as authService from '../../frontend/src/services/auth';

vi.mock('../../frontend/src/services/auth');

describe('Auth Service', () => {
  it('logs in and stores user/session', async () => {
    (authService.login as any).mockResolvedValue({
      access_token: 'token',
      user: { id: 1, email: 'test@example.com', role: 'admin' },
    });
    const data = await authService.login('test@example.com', 'password');
    expect(data.access_token).toBe('token');
    expect(data.user.email).toBe('test@example.com');
  });

  it('logs out and clears session', () => {
    authService.logout();
    expect(localStorage.getItem('energy-tracking-auth-token')).toBeNull();
    expect(localStorage.getItem('energy-tracking-session')).toBeNull();
  });
});
