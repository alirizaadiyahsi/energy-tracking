import React, { useState, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import { Download, TrendingUp, Calendar, BarChart3, AlertCircle } from 'lucide-react';
import { ChartDataPoint } from '../../types';
import { ChartParams } from '../../types/analytics';
import { formatAnalyticsValue } from '../../utils/analyticsTransformers';
import { defaultChartOptions, chartColors } from '../../utils/chartConfig';

interface ConsumptionForecastProps {
  params: ChartParams;
  height?: number;
  showControls?: boolean;
  forecastDays?: number;
  confidenceInterval?: boolean;
  onParamsChange?: (params: ChartParams) => void;
}

interface ForecastControlsProps {
  params: ChartParams;
  onParamsChange: (params: ChartParams) => void;
  forecastDays: number;
  onForecastDaysChange: (days: number) => void;
  confidenceInterval: boolean;
  onConfidenceIntervalChange: (enabled: boolean) => void;
  isLoading: boolean;
}

const ForecastControls: React.FC<ForecastControlsProps> = ({
  params,
  onParamsChange,
  forecastDays,
  onForecastDaysChange,
  confidenceInterval,
  onConfidenceIntervalChange,
  isLoading,
}) => {
  const forecastOptions = [
    { value: 7, label: '7 Days' },
    { value: 14, label: '14 Days' },
    { value: 30, label: '30 Days' },
    { value: 90, label: '90 Days' },
  ];

  const intervals = [
    { value: 'hourly', label: 'Hourly' },
    { value: 'daily', label: 'Daily' },
  ] as const;

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <div className="flex items-center space-x-2">
        <Calendar className="h-4 w-4 text-purple-500" />
        <select
          value={params.interval}
          onChange={(e) => onParamsChange({ ...params, interval: e.target.value as ChartParams['interval'] })}
          disabled={isLoading}
          className="text-sm border border-purple-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          {intervals.map(interval => (
            <option key={interval.value} value={interval.value}>
              {interval.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center space-x-2">
        <BarChart3 className="h-4 w-4 text-purple-500" />
        <select
          value={forecastDays}
          onChange={(e) => onForecastDaysChange(Number(e.target.value))}
          disabled={isLoading}
          className="text-sm border border-purple-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          {forecastOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <label className="flex items-center space-x-2 text-sm">
        <input
          type="checkbox"
          checked={confidenceInterval}
          onChange={(e) => onConfidenceIntervalChange(e.target.checked)}
          className="rounded"
        />
        <span>Confidence Interval</span>
      </label>
    </div>
  );
};

interface ForecastStatsProps {
  forecastData: ChartDataPoint[];
  historicalData: ChartDataPoint[];
  forecastDays: number;
}

const ForecastStats: React.FC<ForecastStatsProps> = ({ forecastData, historicalData, forecastDays }) => {
  const stats = useMemo(() => {
    if (!forecastData || forecastData.length === 0) {
      return {
        predictedTotal: 0,
        averageDaily: 0,
        trend: 'stable' as const,
        accuracy: 0,
        peakForecast: 0,
      };
    }

    const forecastValues = forecastData.map(point => point.value);
    const predictedTotal = forecastValues.reduce((sum, value) => sum + value, 0);
    const averageDaily = predictedTotal / forecastDays;
    
    // Calculate trend based on historical vs forecast
    const historicalAvg = historicalData.length > 0 
      ? historicalData.reduce((sum, point) => sum + point.value, 0) / historicalData.length
      : 0;
    
    const forecastAvg = forecastValues.reduce((sum, val) => sum + val, 0) / forecastValues.length;
    const trend = forecastAvg > historicalAvg * 1.05 ? 'up' : forecastAvg < historicalAvg * 0.95 ? 'down' : 'stable';
    
    const accuracy = 85 + Math.random() * 10; // Mock accuracy between 85-95%
    const peakForecast = Math.max(...forecastValues);

    return {
      predictedTotal,
      averageDaily,
      trend,
      accuracy,
      peakForecast,
    };
  }, [forecastData, historicalData, forecastDays]);

  const getTrendIcon = () => {
    if (stats.trend === 'up') return <TrendingUp className="h-4 w-4 text-red-600" />;
    if (stats.trend === 'down') return <TrendingUp className="h-4 w-4 text-green-600 transform rotate-180" />;
    return <div className="h-4 w-4 bg-gray-400 rounded-full" />;
  };

  const getTrendColor = () => {
    switch (stats.trend) {
      case 'up': return 'text-red-600';
      case 'down': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4 p-3 bg-purple-50 rounded-lg">
      <div className="text-center">
        <p className="text-xs text-purple-600 font-medium">Predicted Total</p>
        <p className="text-sm font-semibold text-purple-900">
          {formatAnalyticsValue(stats.predictedTotal, 'energy')}
        </p>
      </div>
      <div className="text-center">
        <p className="text-xs text-purple-600 font-medium">Daily Average</p>
        <p className="text-sm font-semibold text-purple-900">
          {formatAnalyticsValue(stats.averageDaily, 'energy')}
        </p>
      </div>
      <div className="text-center">
        <p className="text-xs text-purple-600 font-medium">Peak Forecast</p>
        <p className="text-sm font-semibold text-purple-900">
          {formatAnalyticsValue(stats.peakForecast, 'energy')}
        </p>
      </div>
      <div className="text-center">
        <div className="flex items-center justify-center space-x-1">
          {getTrendIcon()}
          <p className="text-xs text-purple-600 font-medium">Trend</p>
        </div>
        <p className={`text-xs font-medium capitalize ${getTrendColor()}`}>{stats.trend}</p>
      </div>
      <div className="text-center">
        <p className="text-xs text-purple-600 font-medium">Accuracy</p>
        <p className="text-sm font-semibold text-purple-900">{stats.accuracy.toFixed(1)}%</p>
      </div>
    </div>
  );
};

const ConsumptionForecast: React.FC<ConsumptionForecastProps> = ({
  params,
  height = 400,
  showControls = true,
  forecastDays: initialForecastDays = 30,
  confidenceInterval: initialConfidenceInterval = true,
  onParamsChange,
}) => {
  const [forecastDays, setForecastDays] = useState(initialForecastDays);
  const [confidenceInterval, setConfidenceInterval] = useState(initialConfidenceInterval);

  // For now, we'll use mock data since the API structure doesn't match our needs
  // const { data: forecastData, isLoading, error } = useForecastData({
  //   ...params,
  //   forecastDays,
  //   confidenceInterval,
  // });

  const isLoading = false;
  const error = null;

  // Generate mock forecast data for demonstration
  const mockData = useMemo(() => {
    const now = new Date();
    const historicalData: ChartDataPoint[] = [];
    const forecastedData: ChartDataPoint[] = [];
    const upperBound: ChartDataPoint[] = [];
    const lowerBound: ChartDataPoint[] = [];

    // Generate 30 days of historical data
    const historicalDays = 30;
    const intervalMs = params.interval === 'hourly' ? 60 * 60 * 1000 : 24 * 60 * 60 * 1000;
    const pointsPerDay = params.interval === 'hourly' ? 24 : 1;
    
    // Historical data
    for (let i = historicalDays * pointsPerDay; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - (i * intervalMs)).toISOString();
      const baseValue = 25 + Math.sin(i * 0.1) * 5; // Base consumption with seasonal variation
      const dailyVariation = Math.sin(i * 0.3) * 3; // Daily variation
      const randomNoise = (Math.random() - 0.5) * 4; // Random noise
      const value = Math.max(0, baseValue + dailyVariation + randomNoise);
      
      historicalData.push({
        timestamp,
        value: Math.round(value * 100) / 100,
      });
    }

    // Forecast data
    const trend = 1.02; // 2% growth trend
    const lastHistoricalValue = historicalData[historicalData.length - 1]?.value || 25;
    
    for (let i = 1; i <= forecastDays * pointsPerDay; i++) {
      const timestamp = new Date(now.getTime() + (i * intervalMs)).toISOString();
      const trendValue = lastHistoricalValue * Math.pow(trend, i / (pointsPerDay * 30)); // Monthly trend
      const seasonalVariation = Math.sin(i * 0.1) * 3;
      const forecastValue = Math.max(0, trendValue + seasonalVariation);
      
      // Confidence intervals
      const uncertaintyFactor = Math.min(0.3, i / (forecastDays * pointsPerDay) * 0.3); // Increasing uncertainty
      const upper = forecastValue * (1 + uncertaintyFactor);
      const lower = forecastValue * (1 - uncertaintyFactor);

      forecastedData.push({
        timestamp,
        value: Math.round(forecastValue * 100) / 100,
      });

      if (confidenceInterval) {
        upperBound.push({
          timestamp,
          value: Math.round(upper * 100) / 100,
        });
        lowerBound.push({
          timestamp,
          value: Math.round(lower * 100) / 100,
        });
      }
    }

    return {
      historical: historicalData,
      forecast: forecastedData,
      upperBound,
      lowerBound,
    };
  }, [params.interval, forecastDays, confidenceInterval]);

  const handleExport = () => {
    if (!mockData) return;
    
    const csvContent = [
      ['Timestamp', 'Type', 'Energy Consumption (kWh)', 'Upper Bound', 'Lower Bound'],
      ...mockData.historical.map(point => [
        new Date(point.timestamp).toISOString(),
        'Historical',
        point.value.toString(),
        '',
        ''
      ]),
      ...mockData.forecast.map((point, index) => [
        new Date(point.timestamp).toISOString(),
        'Forecast',
        point.value.toString(),
        mockData.upperBound[index]?.value?.toString() || '',
        mockData.lowerBound[index]?.value?.toString() || ''
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `consumption-forecast-${forecastDays}days.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {showControls && onParamsChange && (
          <ForecastControls
            params={params}
            onParamsChange={onParamsChange}
            forecastDays={forecastDays}
            onForecastDaysChange={setForecastDays}
            confidenceInterval={confidenceInterval}
            onConfidenceIntervalChange={setConfidenceInterval}
            isLoading={true}
          />
        )}
        <div className={`h-${height} flex items-center justify-center bg-purple-50 rounded-lg`}>
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-2"></div>
            <p className="text-sm text-purple-500">Generating forecast...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        {showControls && onParamsChange && (
          <ForecastControls
            params={params}
            onParamsChange={onParamsChange}
            forecastDays={forecastDays}
            onForecastDaysChange={setForecastDays}
            confidenceInterval={confidenceInterval}
            onConfidenceIntervalChange={setConfidenceInterval}
            isLoading={false}
          />
        )}
        <div className={`h-${height} flex items-center justify-center bg-red-50 rounded-lg border border-red-200`}>
          <div className="text-center">
            <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-sm text-red-600 mb-2">Failed to generate forecast</p>
            <p className="text-xs text-red-500">Unable to load forecast data</p>
          </div>
        </div>
      </div>
    );
  }

  // Use mock data since API structure doesn't match component needs yet
  const data = mockData;
  
  if (!data.historical || !data.forecast) {
    return (
      <div className="space-y-4">
        {showControls && onParamsChange && (
          <ForecastControls
            params={params}
            onParamsChange={onParamsChange}
            forecastDays={forecastDays}
            onForecastDaysChange={setForecastDays}
            confidenceInterval={confidenceInterval}
            onConfidenceIntervalChange={setConfidenceInterval}
            isLoading={false}
          />
        )}
        <div className={`h-${height} flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300`}>
          <div className="text-center">
            <p className="text-sm text-secondary-500 mb-1">No forecast data available</p>
            <p className="text-xs text-secondary-400">Insufficient historical data for forecasting</p>
          </div>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const allTimestamps = [...data.historical, ...data.forecast].map(point => point.timestamp);
  
  const chartData = {
    labels: allTimestamps,
    datasets: [
      {
        label: 'Historical',
        data: [
          ...data.historical.map((point: ChartDataPoint) => ({ x: point.timestamp, y: point.value })),
          ...Array(data.forecast.length).fill({ x: null, y: null })
        ],
        borderColor: chartColors.energy.border,
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.4,
        pointRadius: 1,
        borderWidth: 2,
      },
      {
        label: 'Forecast',
        data: [
          ...Array(data.historical.length).fill({ x: null, y: null }),
          ...data.forecast.map((point: ChartDataPoint) => ({ x: point.timestamp, y: point.value }))
        ],
        borderColor: chartColors.primary.border,
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.4,
        pointRadius: 2,
        borderWidth: 2,
        borderDash: [5, 5],
      },
    ],
  };

  // Add confidence interval if enabled
  if (confidenceInterval && data.upperBound && data.lowerBound) {
    chartData.datasets.push(
      {
        label: 'Upper Bound',
        data: [
          ...Array(data.historical.length).fill({ x: null, y: null }),
          ...data.upperBound.map((point: ChartDataPoint) => ({ x: point.timestamp, y: point.value }))
        ],
        borderColor: 'rgba(59, 130, 246, 0.3)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 1,
      },
      {
        label: 'Lower Bound',
        data: [
          ...Array(data.historical.length).fill({ x: null, y: null }),
          ...data.lowerBound.map((point: ChartDataPoint) => ({ x: point.timestamp, y: point.value }))
        ],
        borderColor: 'rgba(59, 130, 246, 0.3)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 0,
        borderWidth: 1,
      }
    );
  }

  const options = {
    ...defaultChartOptions,
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      ...defaultChartOptions.scales,
      y: {
        ...defaultChartOptions.scales?.y,
        title: {
          display: true,
          text: 'Energy Consumption (kWh)',
          color: '#7c3aed',
          font: {
            size: 12,
            weight: 'normal' as const,
          },
        },
        beginAtZero: true,
      },
      x: {
        ...defaultChartOptions.scales?.x,
        title: {
          display: true,
          text: 'Time',
          color: '#7c3aed',
          font: {
            size: 12,
            weight: 'normal' as const,
          },
        },
      },
    },
    plugins: {
      ...defaultChartOptions.plugins,
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          filter: function(legendItem: any) {
            // Hide confidence interval bounds from legend
            return !legendItem.text.includes('Bound');
          },
        },
      },
      tooltip: {
        ...defaultChartOptions.plugins?.tooltip,
        callbacks: {
          label: (context: any) => {
            const label = context.dataset.label || '';
            const value = formatAnalyticsValue(context.parsed.y, 'energy');
            return `${label}: ${value}`;
          },
        },
      },
    },
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <TrendingUp className="h-5 w-5 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">Consumption Forecast</h3>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center space-x-1 px-3 py-1 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
        >
          <Download className="h-4 w-4" />
          <span>Export</span>
        </button>
      </div>

      {/* Controls */}
      {showControls && onParamsChange && (
        <ForecastControls
          params={params}
          onParamsChange={onParamsChange}
          forecastDays={forecastDays}
          onForecastDaysChange={setForecastDays}
          confidenceInterval={confidenceInterval}
          onConfidenceIntervalChange={setConfidenceInterval}
          isLoading={isLoading}
        />
      )}

      {/* Statistics */}
      <ForecastStats 
        forecastData={data.forecast} 
        historicalData={data.historical}
        forecastDays={forecastDays}
      />

      {/* Chart */}
      <div style={{ height: `${height}px` }} className="w-full">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};

export default ConsumptionForecast;
