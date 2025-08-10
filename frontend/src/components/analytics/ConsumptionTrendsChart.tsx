import React, { useState, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import { Download, TrendingUp, Calendar, Filter } from 'lucide-react';
import { ChartDataPoint } from '../../types';
import { ChartParams } from '../../types/analytics';
import { useConsumptionTrends } from '../../hooks/useAnalyticsData';
import { transformChartData, formatAnalyticsValue, calculateMovingAverage } from '../../utils/analyticsTransformers';
import { defaultChartOptions, chartColors } from '../../utils/chartConfig';

interface ConsumptionTrendsChartProps {
  params: ChartParams;
  height?: number;
  showControls?: boolean;
  showStats?: boolean;
  deviceId?: string;
  onParamsChange?: (params: ChartParams) => void;
}

interface ChartControlsProps {
  params: ChartParams;
  onParamsChange: (params: ChartParams) => void;
  isLoading: boolean;
}

const ChartControls: React.FC<ChartControlsProps> = ({ params, onParamsChange, isLoading }) => {
  const intervals = [
    { value: 'minutely', label: 'Minutely' },
    { value: 'hourly', label: 'Hourly' },
    { value: 'daily', label: 'Daily' },
  ] as const;

  const timeRanges = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last Week' },
    { value: '30d', label: 'Last Month' },
  ] as const;

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <div className="flex items-center space-x-2">
        <Calendar className="h-4 w-4 text-secondary-500" />
        <select
          value={params.interval}
          onChange={(e) => onParamsChange({ ...params, interval: e.target.value as ChartParams['interval'] })}
          disabled={isLoading}
          className="text-sm border border-secondary-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {intervals.map(interval => (
            <option key={interval.value} value={interval.value}>
              {interval.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center space-x-2">
        <Filter className="h-4 w-4 text-secondary-500" />
        <select
          value={params.timeRange}
          onChange={(e) => onParamsChange({ ...params, timeRange: e.target.value as ChartParams['timeRange'] })}
          disabled={isLoading}
          className="text-sm border border-secondary-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {timeRanges.map(range => (
            <option key={range.value} value={range.value}>
              {range.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

interface ChartStatsProps {
  data: ChartDataPoint[];
}

const ChartStats: React.FC<ChartStatsProps> = ({ data }) => {
  const stats = useMemo(() => {
    if (!data || data.length === 0) {
      return { total: 0, average: 0, peak: 0, trend: 'stable' as const };
    }

    const values = data.map(point => point.value);
    const total = values.reduce((sum, value) => sum + value, 0);
    const average = total / values.length;
    const peak = Math.max(...values);
    
    // Simple trend calculation
    const firstHalf = values.slice(0, Math.floor(values.length / 2));
    const secondHalf = values.slice(Math.floor(values.length / 2));
    const firstAvg = firstHalf.reduce((sum, val) => sum + val, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((sum, val) => sum + val, 0) / secondHalf.length;
    
    const trend = secondAvg > firstAvg * 1.05 ? 'up' : secondAvg < firstAvg * 0.95 ? 'down' : 'stable';

    return { total, average, peak, trend };
  }, [data]);

  const getTrendIcon = () => {
    if (stats.trend === 'up') return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (stats.trend === 'down') return <TrendingUp className="h-4 w-4 text-red-600 transform rotate-180" />;
    return <div className="h-4 w-4 bg-gray-400 rounded-full" />;
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 p-3 bg-secondary-50 rounded-lg">
      <div className="text-center">
        <p className="text-xs text-secondary-600 font-medium">Total</p>
        <p className="text-sm font-semibold text-secondary-900">
          {formatAnalyticsValue(stats.total, 'energy')}
        </p>
      </div>
      <div className="text-center">
        <p className="text-xs text-secondary-600 font-medium">Average</p>
        <p className="text-sm font-semibold text-secondary-900">
          {formatAnalyticsValue(stats.average, 'energy')}
        </p>
      </div>
      <div className="text-center">
        <p className="text-xs text-secondary-600 font-medium">Peak</p>
        <p className="text-sm font-semibold text-secondary-900">
          {formatAnalyticsValue(stats.peak, 'energy')}
        </p>
      </div>
      <div className="text-center">
        <div className="flex items-center justify-center space-x-1">
          {getTrendIcon()}
          <p className="text-xs text-secondary-600 font-medium">Trend</p>
        </div>
        <p className="text-xs font-medium capitalize text-secondary-700">{stats.trend}</p>
      </div>
    </div>
  );
};

const ConsumptionTrendsChart: React.FC<ConsumptionTrendsChartProps> = ({
  params,
  height = 320,
  showControls = true,
  showStats = true,
  deviceId,
  onParamsChange,
}) => {
  const [showSmoothing, setShowSmoothing] = useState(false);
  
  const finalParams = { ...params, deviceId };
  const { data: rawData, isLoading, error } = useConsumptionTrends(finalParams);

  const processedData = useMemo(() => {
    if (!rawData || rawData.length === 0) return [];
    return showSmoothing ? calculateMovingAverage(rawData, 5) : rawData;
  }, [rawData, showSmoothing]);

  const handleExport = () => {
    if (!processedData || processedData.length === 0) return;
    
    const csvContent = [
      ['Timestamp', 'Energy Consumption (kWh)'],
      ...processedData.map(point => [
        new Date(point.timestamp).toISOString(),
        point.value.toString()
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `energy-consumption-${params.interval}-${params.timeRange}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {showControls && onParamsChange && (
          <ChartControls params={params} onParamsChange={onParamsChange} isLoading={true} />
        )}
        <div className={`h-${height} flex items-center justify-center bg-gray-50 rounded-lg`}>
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
            <p className="text-sm text-secondary-500">Loading consumption data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        {showControls && onParamsChange && (
          <ChartControls params={params} onParamsChange={onParamsChange} isLoading={false} />
        )}
        <div className={`h-${height} flex items-center justify-center bg-red-50 rounded-lg border border-red-200`}>
          <div className="text-center">
            <p className="text-sm text-red-600 mb-2">Failed to load consumption data</p>
            <p className="text-xs text-red-500">{error.message}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!processedData || processedData.length === 0) {
    return (
      <div className="space-y-4">
        {showControls && onParamsChange && (
          <ChartControls params={params} onParamsChange={onParamsChange} isLoading={false} />
        )}
        <div className={`h-${height} flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300`}>
          <div className="text-center">
            <p className="text-sm text-secondary-500 mb-1">No consumption data available</p>
            <p className="text-xs text-secondary-400">Try adjusting the time range or interval</p>
          </div>
        </div>
      </div>
    );
  }

  const chartData = transformChartData(processedData, 'area');
  
  // Enhance the chart data with custom styling
  chartData.datasets[0] = {
    ...chartData.datasets[0],
    label: 'Energy Consumption',
    borderColor: chartColors.energy.border,
    backgroundColor: chartColors.energy.background,
    fill: true,
    tension: 0.4,
    pointBackgroundColor: chartColors.energy.border,
    pointBorderColor: '#fff',
    pointBorderWidth: 2,
    pointRadius: 3,
    pointHoverRadius: 6,
  };

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
          color: '#6B7280',
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
          color: '#6B7280',
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
        display: false,
      },
      tooltip: {
        ...defaultChartOptions.plugins?.tooltip,
        callbacks: {
          label: (context: any) => `${formatAnalyticsValue(context.parsed.y, 'energy')}`,
          title: (context: any) => {
            const point = processedData[context[0].dataIndex];
            return new Date(point.timestamp).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
              hour: params.interval === 'minutely' ? 'numeric' : undefined,
              minute: params.interval === 'minutely' ? 'numeric' : undefined,
            });
          },
        },
      },
    },
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      {showControls && onParamsChange && (
        <div className="flex flex-wrap items-center justify-between gap-4">
          <ChartControls params={params} onParamsChange={onParamsChange} isLoading={isLoading} />
          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={showSmoothing}
                onChange={(e) => setShowSmoothing(e.target.checked)}
                className="rounded"
              />
              <span>Smooth data</span>
            </label>
            <button
              onClick={handleExport}
              className="flex items-center space-x-1 px-3 py-1 text-sm bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
              disabled={!processedData || processedData.length === 0}
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
          </div>
        </div>
      )}

      {/* Statistics */}
      {showStats && <ChartStats data={processedData} />}

      {/* Chart */}
      <div style={{ height: `${height}px` }} className="w-full">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};

export default ConsumptionTrendsChart;
