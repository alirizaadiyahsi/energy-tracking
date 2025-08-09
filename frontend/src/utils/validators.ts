// Validation utilities for forms and data in the energy tracking app

export function isValidEmail(email: string): boolean {
  return /^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$/.test(email);
}

export function isValidPassword(password: string): boolean {
  // At least 8 chars, 1 uppercase, 1 lowercase, 1 number
  return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[A-Za-z\d@$!%*?&]{8,}$/.test(password);
}

export function isNonEmptyString(value: string): boolean {
  return typeof value === 'string' && value.trim().length > 0;
}

export function isPositiveNumber(value: number): boolean {
  return typeof value === 'number' && value > 0;
}

export function isValidDeviceName(name: string): boolean {
  // Device names: 3-32 chars, alphanumeric and dashes/underscores
  return /^[A-Za-z0-9-_]{3,32}$/.test(name);
}
