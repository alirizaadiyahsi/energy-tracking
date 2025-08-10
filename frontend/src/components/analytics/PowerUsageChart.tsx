import React, { useState, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import { Download, Zap, Settings, Activity } from 'lucide-react';
import { ChartDataPoint } from '../../types';
import { ChartParams } from '../../types/analytics';
import { usePowerTrends } from '../../hooks/useAnalyticsData';
import { transformChartData, formatAnalyticsValue, calculatePeakDetection } from '../../utils/analyticsTransformers';
import { defaultChartOptions, chartColors } from '../../utils/chartConfig';

interface PowerUsageChartProps {
  params: ChartParams;
  height?: number;
  showControls?: boolean;
  showPeakDetection?: boolean;
  deviceId?: string;
  onParamsChange?: (params: ChartParams) => void;
}

interface PowerStatsProps {
  data: ChartDataPoint[];
  showPeakDetection: boolean;
}

const PowerStats: React.FC<PowerStatsProps> = ({ data, showPeakDetection }) => {
  const stats = useMemo(() => {
    if (!data || data.length === 0) {
      return { 
        currentPower: 0, 
        averagePower: 0, 
        peakPower: 0, 
        efficiency: 0,
        peakEvents: [] as Array<{ timestamp: string; value: number }>
      };
    }

    const values = data.map(point => point.value);
    const currentPower = values[values.length - 1] || 0;
    const averagePower = values.reduce((sum, value) => sum + value, 0) / values.length;
    const peakPower = Math.max(...values);
    
    // Calculate efficiency as inverse of variance (lower variance = more efficient)
    const variance = values.reduce((sum, value) => sum + Math.pow(value - averagePower, 2), 0) / values.length;
    const efficiency = variance > 0 ? Math.max(0, 100 - (variance / averagePower) * 100) : 100;
    
    // Peak detection
    const peakEvents = showPeakDetection ? calculatePeakDetection(data, peakPower * 0.8) : [];

    return { currentPower, averagePower, peakPower, efficiency, peakEvents };
  }, [data, showPeakDetection]);

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 p-3 bg-blue-50 rounded-lg">
      <div className="text-center">
        <p className="text-xs text-blue-600 font-medium">Current Power</p>
        <p className="text-sm font-semibold text-blue-900 flex items-center justify-center">
          <Activity className="h-3 w-3 mr-1" />
          {formatAnalyticsValue(stats.currentPower, 'power')}
        </p>
      </div>
      <div className="text-center">
        <p className="text-xs text-blue-600 font-medium">Average</p>
        <p className="text-sm font-semibold text-blue-900">
          {formatAnalyticsValue(stats.averagePower, 'power')}
        </p>
      </div>
      <div className="text-center">
        <p className="text-xs text-blue-600 font-medium">Peak Power</p>
        <p className="text-sm font-semibold text-blue-900 flex items-center justify-center">
          <Zap className="h-3 w-3 mr-1" />
          {formatAnalyticsValue(stats.peakPower, 'power')}
        </p>
      </div>
      <div className="text-center">
        <p className="text-xs text-blue-600 font-medium">Efficiency</p>
        <p className="text-sm font-semibold text-blue-900">
          {stats.efficiency.toFixed(1)}%
        </p>
      </div>
      {stats.peakEvents.length > 0 && (
        <div className="col-span-2 md:col-span-4 mt-2 pt-2 border-t border-blue-200">
          <p className="text-xs text-blue-600 font-medium mb-1">
            Peak Events Detected: {stats.peakEvents.length}
          </p>
          <div className="flex flex-wrap gap-1">
            {stats.peakEvents.slice(0, 3).map((peak: { timestamp: string; value: number }, index: number) => (
              <span 
                key={index}
                className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full"
              >
                {formatAnalyticsValue(peak.value, 'power')} at {new Date(peak.timestamp).toLocaleTimeString()}
              </span>
            ))}
            {stats.peakEvents.length > 3 && (
              <span className="text-xs text-blue-500">+{stats.peakEvents.length - 3} more</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

interface PowerControlsProps {
  params: ChartParams;
  onParamsChange: (params: ChartParams) => void;
  isLoading: boolean;
  showPeakDetection: boolean;
  onTogglePeakDetection: (show: boolean) => void;
}

const PowerControls: React.FC<PowerControlsProps> = ({ 
  params, 
  onParamsChange, 
  isLoading, 
  showPeakDetection, 
  onTogglePeakDetection 
}) => {
  const intervals = [
    { value: 'minutely', label: 'Minutely' },
    { value: 'hourly', label: 'Hourly' },
  ] as const;

  const timeRanges = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last Week' },
  ] as const;

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <div className="flex items-center space-x-2">
        <Settings className="h-4 w-4 text-blue-500" />
        <select
          value={params.interval}
          onChange={(e) => onParamsChange({ ...params, interval: e.target.value as ChartParams['interval'] })}
          disabled={isLoading}
          className="text-sm border border-blue-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {intervals.map(interval => (
            <option key={interval.value} value={interval.value}>
              {interval.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center space-x-2">
        <select
          value={params.timeRange}
          onChange={(e) => onParamsChange({ ...params, timeRange: e.target.value as ChartParams['timeRange'] })}
          disabled={isLoading}
          className="text-sm border border-blue-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {timeRanges.map(range => (
            <option key={range.value} value={range.value}>
              {range.label}
            </option>
          ))}
        </select>
      </div>

      <label className="flex items-center space-x-2 text-sm">
        <input
          type="checkbox"
          checked={showPeakDetection}
          onChange={(e) => onTogglePeakDetection(e.target.checked)}
          className="rounded"
        />
        <span>Peak Detection</span>
      </label>
    </div>
  );
};

const PowerUsageChart: React.FC<PowerUsageChartProps> = ({
  params,
  height = 320,
  showControls = true,
  showPeakDetection = false,
  deviceId,
  onParamsChange,
}) => {
  const [internalPeakDetection, setInternalPeakDetection] = useState(showPeakDetection);
  const [realTimeMode, setRealTimeMode] = useState(false);
  
  const finalParams = { ...params, deviceId };
  const { data: rawData, isLoading, error } = usePowerTrends(finalParams);

  const processedData = useMemo(() => {
    if (!rawData || rawData.length === 0) return [];
    
    // For real-time mode, show data with minimal delay simulation
    if (realTimeMode && params.interval === 'minutely') {
      const now = new Date();
      const recentData = rawData.filter(point => 
        new Date(point.timestamp).getTime() > now.getTime() - (5 * 60 * 1000) // Last 5 minutes
      );
      return recentData.length > 0 ? recentData : rawData.slice(-10);
    }
    
    return rawData;
  }, [rawData, realTimeMode, params.interval]);

  const handleExport = () => {
    if (!processedData || processedData.length === 0) return;
    
    const csvContent = [
      ['Timestamp', 'Power Usage (W)', 'Peak Detection'],
      ...processedData.map(point => [
        new Date(point.timestamp).toISOString(),
        point.value.toString(),
        internalPeakDetection ? 'enabled' : 'disabled'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `power-usage-${params.interval}-${params.timeRange}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        {showControls && onParamsChange && (
          <PowerControls 
            params={params} 
            onParamsChange={onParamsChange} 
            isLoading={true}
            showPeakDetection={internalPeakDetection}
            onTogglePeakDetection={setInternalPeakDetection}
          />
        )}
        <div className={`h-${height} flex items-center justify-center bg-blue-50 rounded-lg`}>
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-blue-500">Loading power data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        {showControls && onParamsChange && (
          <PowerControls 
            params={params} 
            onParamsChange={onParamsChange} 
            isLoading={false}
            showPeakDetection={internalPeakDetection}
            onTogglePeakDetection={setInternalPeakDetection}
          />
        )}
        <div className={`h-${height} flex items-center justify-center bg-red-50 rounded-lg border border-red-200`}>
          <div className="text-center">
            <p className="text-sm text-red-600 mb-2">Failed to load power data</p>
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
          <PowerControls 
            params={params} 
            onParamsChange={onParamsChange} 
            isLoading={false}
            showPeakDetection={internalPeakDetection}
            onTogglePeakDetection={setInternalPeakDetection}
          />
        )}
        <div className={`h-${height} flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300`}>
          <div className="text-center">
            <p className="text-sm text-secondary-500 mb-1">No power data available</p>
            <p className="text-xs text-secondary-400">Try adjusting the time range or interval</p>
          </div>
        </div>
      </div>
    );
  }

  const chartData = transformChartData(processedData, 'line');
  
  // Enhance the chart data with power-specific styling
  chartData.datasets[0] = {
    ...chartData.datasets[0],
    label: 'Power Usage',
    borderColor: chartColors.power.border,
    backgroundColor: 'transparent',
    fill: false,
    tension: 0.3,
    pointBackgroundColor: chartColors.power.border,
    pointBorderColor: '#fff',
    pointBorderWidth: 2,
    pointRadius: realTimeMode ? 4 : 2,
    pointHoverRadius: 6,
    borderWidth: 2,
  };

  // Add peak detection markers if enabled
  if (internalPeakDetection) {
    const peaks = calculatePeakDetection(processedData, Math.max(...processedData.map(p => p.value)) * 0.8);
    if (peaks.length > 0) {
      chartData.datasets.push({
        label: 'Peak Events',
        data: peaks.map((peak: { timestamp: string; value: number }) => ({
          x: peak.timestamp,
          y: peak.value,
        })),
        borderColor: '#f59e0b',
        backgroundColor: '#fbbf24',
        pointRadius: 6,
        pointHoverRadius: 8,
        showLine: false,
        pointStyle: 'triangle',
      });
    }
  }

  const options = {
    ...defaultChartOptions,
    responsive: true,
    maintainAspectRatio: false,
    animation: realTimeMode ? { duration: 0 } : { duration: 750 },
    scales: {
      ...defaultChartOptions.scales,
      y: {
        ...defaultChartOptions.scales?.y,
        title: {
          display: true,
          text: 'Power Usage (W)',
          color: '#1e40af',
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
          color: '#1e40af',
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
        display: internalPeakDetection,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
        },
      },
      tooltip: {
        ...defaultChartOptions.plugins?.tooltip,
        callbacks: {
          label: (context: any) => {
            const datasetLabel = context.dataset.label || '';
            const value = formatAnalyticsValue(context.parsed.y, 'power');
            return `${datasetLabel}: ${value}`;
          },
          title: (context: any) => {
            const point = processedData[context[0].dataIndex];
            if (!point) return '';
            return new Date(point.timestamp).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: 'numeric',
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
          <PowerControls 
            params={params} 
            onParamsChange={onParamsChange} 
            isLoading={isLoading}
            showPeakDetection={internalPeakDetection}
            onTogglePeakDetection={setInternalPeakDetection}
          />
          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-2 text-sm">
              <input
                type="checkbox"
                checked={realTimeMode}
                onChange={(e) => setRealTimeMode(e.target.checked)}
                className="rounded"
                disabled={params.interval !== 'minutely'}
              />
              <span>Real-time Mode</span>
            </label>
            <button
              onClick={handleExport}
              className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              disabled={!processedData || processedData.length === 0}
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
          </div>
        </div>
      )}

      {/* Statistics */}
      <PowerStats data={processedData} showPeakDetection={internalPeakDetection} />

      {/* Chart */}
      <div style={{ height: `${height}px` }} className="w-full">
        <Line 
          key={`power-chart-${params.interval}-${params.timeRange}-${showPeakDetection}`}
          data={chartData} 
          options={options} 
        />
      </div>
    </div>
  );
};

export default PowerUsageChart;
