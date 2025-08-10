import { ChartDataPoint } from '../types';
import { ForecastData, ComparisonResult } from '../types/analytics';

/**
 * Format numbers for display with appropriate units and precision
 */
export const formatAnalyticsValue = (
  value: number,
  type: 'energy' | 'power' | 'percentage' | 'currency' | 'count',
  precision: number = 2
): string => {
  if (isNaN(value) || !isFinite(value)) {
    return 'N/A';
  }

  switch (type) {
    case 'energy':
      if (value >= 1000) {
        return `${(value / 1000).toFixed(precision)} MWh`;
      }
      return `${value.toFixed(precision)} kWh`;

    case 'power':
      if (value >= 1000000) {
        return `${(value / 1000000).toFixed(precision)} MW`;
      }
      if (value >= 1000) {
        return `${(value / 1000).toFixed(precision)} kW`;
      }
      return `${value.toFixed(precision)} W`;

    case 'percentage':
      return `${value.toFixed(precision)}%`;

    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: precision,
        maximumFractionDigits: precision,
      }).format(value);

    case 'count':
      return Math.round(value).toLocaleString();

    default:
      return value.toFixed(precision);
  }
};

/**
 * Calculate percentage change between two values
 */
export const calculatePercentageChange = (
  current: number,
  previous: number
): { value: number; isIncrease: boolean; isDecrease: boolean } => {
  if (previous === 0) {
    return { value: current > 0 ? 100 : 0, isIncrease: current > 0, isDecrease: false };
  }

  const change = ((current - previous) / Math.abs(previous)) * 100;
  return {
    value: Math.abs(change),
    isIncrease: change > 0,
    isDecrease: change < 0,
  };
};

/**
 * Transform chart data for different visualization types
 */
export const transformChartData = (
  data: ChartDataPoint[],
  chartType: 'line' | 'bar' | 'area' = 'line'
): any => {
  if (!data || data.length === 0) {
    return {
      labels: [],
      datasets: [],
    };
  }

  const labels = data.map(point => {
    const date = new Date(point.timestamp);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: data.length <= 24 ? 'numeric' : undefined
    });
  });

  const values = data.map(point => point.value);

  const baseDataset = {
    label: 'Value',
    data: values,
    borderColor: 'rgb(59, 130, 246)',
    backgroundColor: chartType === 'area' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(59, 130, 246, 0.8)',
    tension: chartType === 'line' ? 0.1 : 0,
    fill: chartType === 'area',
  };

  return {
    labels,
    datasets: [baseDataset],
  };
};

/**
 * Calculate moving average for smoothing data
 */
export const calculateMovingAverage = (
  data: ChartDataPoint[],
  windowSize: number = 5
): ChartDataPoint[] => {
  if (data.length < windowSize) return data;

  return data.map((_, index) => {
    const start = Math.max(0, index - Math.floor(windowSize / 2));
    const end = Math.min(data.length, start + windowSize);
    const window = data.slice(start, end);
    const average = window.reduce((sum, point) => sum + point.value, 0) / window.length;

    return {
      ...data[index],
      value: average,
    };
  });
};

/**
 * Aggregate data by time period
 */
export const aggregateDataByPeriod = (
  data: ChartDataPoint[],
  period: 'hour' | 'day' | 'week' | 'month'
): ChartDataPoint[] => {
  const aggregated = new Map<string, { sum: number; count: number; timestamp: string }>();

  data.forEach(point => {
    const date = new Date(point.timestamp);
    let key: string;

    switch (period) {
      case 'hour':
        key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`;
        break;
      case 'day':
        key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
        break;
      case 'week':
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        key = `${weekStart.getFullYear()}-${weekStart.getMonth()}-${weekStart.getDate()}`;
        break;
      case 'month':
        key = `${date.getFullYear()}-${date.getMonth()}`;
        break;
      default:
        key = point.timestamp;
    }

    if (!aggregated.has(key)) {
      aggregated.set(key, { sum: 0, count: 0, timestamp: point.timestamp });
    }

    const existing = aggregated.get(key)!;
    existing.sum += point.value;
    existing.count += 1;
  });

  return Array.from(aggregated.entries()).map(([_, value]) => ({
    timestamp: value.timestamp,
    value: value.sum / value.count,
    label: new Date(value.timestamp).toLocaleDateString(),
  }));
};

/**
 * Calculate efficiency score based on consumption and capacity
 */
export const calculateEfficiencyScore = (
  actualConsumption: number,
  theoreticalOptimal: number
): number => {
  if (theoreticalOptimal === 0) return 0;
  const efficiency = (theoreticalOptimal / actualConsumption) * 100;
  return Math.min(100, Math.max(0, efficiency));
};

/**
 * Determine trend direction from data series
 */
export const calculateTrend = (
  data: number[]
): 'up' | 'down' | 'stable' => {
  if (data.length < 2) return 'stable';

  const firstHalf = data.slice(0, Math.floor(data.length / 2));
  const secondHalf = data.slice(Math.floor(data.length / 2));

  const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
  const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;

  const changeThreshold = 0.05; // 5% change threshold
  const percentChange = Math.abs(secondAvg - firstAvg) / firstAvg;

  if (percentChange < changeThreshold) return 'stable';
  return secondAvg > firstAvg ? 'up' : 'down';
};

/**
 * Format forecast data for visualization
 */
export const formatForecastData = (forecast: ForecastData): any => {
  const now = new Date();
  const forecastDays = parseInt(forecast.forecast_period.split(' ')[1] || '30');
  
  const labels = Array.from({ length: forecastDays }, (_, i) => {
    const date = new Date(now);
    date.setDate(date.getDate() + i + 1);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  // Generate sample forecast data points
  const predictedValues = Array.from({ length: forecastDays }, () => {
    const baseValue = forecast.predicted_consumption;
    const variation = (Math.random() - 0.5) * 0.2 * baseValue; // ±20% variation
    return baseValue + variation;
  });

  const confidenceUpper = predictedValues.map(val => 
    val + (forecast.confidence_interval.upper - forecast.predicted_consumption)
  );
  const confidenceLower = predictedValues.map(val => 
    val + (forecast.confidence_interval.lower - forecast.predicted_consumption)
  );

  return {
    labels,
    datasets: [
      {
        label: 'Predicted Consumption',
        data: predictedValues,
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.1,
      },
      {
        label: 'Upper Confidence',
        data: confidenceUpper,
        borderColor: 'rgba(34, 197, 94, 0.3)',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        tension: 0.1,
      },
      {
        label: 'Lower Confidence',
        data: confidenceLower,
        borderColor: 'rgba(34, 197, 94, 0.3)',
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        tension: 0.1,
      },
    ],
  };
};

/**
 * Create comparison chart data from comparison result
 */
export const formatComparisonData = (comparison: ComparisonResult): any => {
  const metrics = ['Energy', 'Power', 'Efficiency', 'Cost'];
  const currentValues = [
    comparison.metrics.energy_consumption.current,
    comparison.metrics.average_power.current,
    comparison.metrics.efficiency.current,
    comparison.metrics.cost.current,
  ];
  const previousValues = [
    comparison.metrics.energy_consumption.previous,
    comparison.metrics.average_power.previous,
    comparison.metrics.efficiency.previous,
    comparison.metrics.cost.previous,
  ];

  return {
    labels: metrics,
    datasets: [
      {
        label: comparison.current_period.label,
        data: currentValues,
        backgroundColor: 'rgba(59, 130, 246, 0.8)',
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1,
      },
      {
        label: comparison.previous_period.label,
        data: previousValues,
        backgroundColor: 'rgba(156, 163, 175, 0.8)',
        borderColor: 'rgb(156, 163, 175)',
        borderWidth: 1,
      },
    ],
  };
};

/**
 * Validate and sanitize analytics data
 */
export const validateAnalyticsData = <T>(data: T, fieldValidators: Record<string, (value: any) => boolean>): T => {
  if (!data || typeof data !== 'object') {
    throw new Error('Invalid data object');
  }

  const validated = { ...data } as any;

  Object.entries(fieldValidators).forEach(([field, validator]) => {
    if (field in validated && !validator(validated[field])) {
      console.warn(`Invalid data in field ${field}:`, validated[field]);
      validated[field] = null;
    }
  });

  return validated;
};

/**
 * Generate color palette for charts
 */
export const generateChartColors = (count: number): string[] => {
  const baseColors = [
    'rgb(59, 130, 246)',   // blue
    'rgb(34, 197, 94)',    // green
    'rgb(251, 191, 36)',   // yellow
    'rgb(239, 68, 68)',    // red
    'rgb(168, 85, 247)',   // purple
    'rgb(236, 72, 153)',   // pink
    'rgb(20, 184, 166)',   // teal
    'rgb(245, 101, 101)',  // orange
  ];

  if (count <= baseColors.length) {
    return baseColors.slice(0, count);
  }

  // Generate additional colors if needed
  const colors = [...baseColors];
  for (let i = baseColors.length; i < count; i++) {
    const hue = (i * 137.508) % 360; // Golden angle approximation
    colors.push(`hsl(${hue}, 70%, 50%)`);
  }

  return colors;
};

/**
 * Detect peak events in time series data
 */
export const calculatePeakDetection = (
  data: ChartDataPoint[],
  threshold: number
): Array<{ timestamp: string; value: number }> => {
  if (!data || data.length < 3) return [];

  const peaks: Array<{ timestamp: string; value: number }> = [];
  
  for (let i = 1; i < data.length - 1; i++) {
    const current = data[i];
    const previous = data[i - 1];
    const next = data[i + 1];
    
    // A peak is detected when:
    // 1. Current value is higher than both neighbors
    // 2. Current value exceeds the threshold
    if (current.value > previous.value && 
        current.value > next.value && 
        current.value >= threshold) {
      peaks.push({
        timestamp: current.timestamp,
        value: current.value
      });
    }
  }
  
  return peaks;
};
