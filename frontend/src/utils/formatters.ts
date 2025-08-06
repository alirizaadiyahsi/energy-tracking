// Formatting utilities for the energy tracking app

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatEnergy(value: number, unit: 'kWh' | 'Wh' = 'kWh'): string {
  if (unit === 'Wh') return `${value.toFixed(0)} Wh`;
  return `${(value / 1000).toFixed(2)} kWh`;
}

export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return amount.toLocaleString('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
  });
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(2)}%`;
}
