import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, parseISO } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date, formatStr: string = 'PPp'): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, formatStr);
}

export function formatNumber(num: number, decimals: number = 2): string {
  return num.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatPower(watts: number): string {
  if (watts >= 1000000) {
    return `${formatNumber(watts / 1000000, 1)} MW`;
  } else if (watts >= 1000) {
    return `${formatNumber(watts / 1000, 1)} kW`;
  }
  return `${formatNumber(watts, 0)} W`;
}

export function formatEnergy(wh: number): string {
  if (wh >= 1000000) {
    return `${formatNumber(wh / 1000000, 2)} MWh`;
  } else if (wh >= 1000) {
    return `${formatNumber(wh / 1000, 2)} kWh`;
  }
  return `${formatNumber(wh, 0)} Wh`;
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'online':
      return 'text-green-600';
    case 'offline':
      return 'text-red-600';
    case 'error':
      return 'text-red-600';
    case 'warning':
      return 'text-yellow-600';
    default:
      return 'text-secondary-600';
  }
}

export function getStatusBadgeColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'online':
      return 'bg-green-100 text-green-800';
    case 'offline':
      return 'bg-red-100 text-red-800';
    case 'error':
      return 'bg-red-100 text-red-800';
    case 'warning':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-secondary-100 text-secondary-800';
  }
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
