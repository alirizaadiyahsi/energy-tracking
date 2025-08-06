// Unit tests for frontend utility functions
import { describe, it, expect } from 'vitest';
import { isValidEmail, isValidPassword, isNonEmptyString, isPositiveNumber, isValidDeviceName } from '../../frontend/src/utils/validators';
import { formatDate, formatEnergy, formatCurrency, formatPercentage } from '../../frontend/src/utils/formatters';

// Validators

describe('validators', () => {
  it('validates email addresses', () => {
    expect(isValidEmail('test@example.com')).toBe(true);
    expect(isValidEmail('bad-email')).toBe(false);
  });
  it('validates passwords', () => {
    expect(isValidPassword('Password1')).toBe(true);
    expect(isValidPassword('pass')).toBe(false);
  });
  it('checks non-empty strings', () => {
    expect(isNonEmptyString('hello')).toBe(true);
    expect(isNonEmptyString('')).toBe(false);
  });
  it('checks positive numbers', () => {
    expect(isPositiveNumber(5)).toBe(true);
    expect(isPositiveNumber(-1)).toBe(false);
  });
  it('validates device names', () => {
    expect(isValidDeviceName('dev-01')).toBe(true);
    expect(isValidDeviceName('!bad')).toBe(false);
  });
});

describe('formatters', () => {
  it('formats dates', () => {
    expect(formatDate('2025-08-07T12:00:00Z')).toContain('2025');
  });
  it('formats energy', () => {
    expect(formatEnergy(1500)).toBe('1.50 kWh');
    expect(formatEnergy(500, 'Wh')).toBe('500 Wh');
  });
  it('formats currency', () => {
    expect(formatCurrency(100)).toContain('$');
  });
  it('formats percentage', () => {
    expect(formatPercentage(12.3456)).toBe('12.35%');
  });
});
