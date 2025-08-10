import React, { useState, useMemo, Dispatch, SetStateAction } from 'react';
import { Line } from 'react-chartjs-2';
import { Download, TrendingUp, BarChart3, AlertCircle } from 'lucide-react';
import { ChartDataPoint } from '../../types';
import { ChartParams } from '../../types/analytics';
import { useConsumptionTrends, useForecastData } from '../../hooks/useAnalyticsData';
import { formatAnalyticsValue } from '../../utils/analyticsTransformers';
import { defaultChartOptions, chartColors } from '../../utils/chartConfig';

interface ForecastDataPoint {
  timestamp: string;
  value: number;
}

interface ProcessedData {
  historical: ForecastDataPoint[];
  forecast: ForecastDataPoint[];
  confidenceUpper?: ForecastDataPoint[];
  confidenceLower?: ForecastDataPoint[];
}

interface ForecastProps {
  params?: ChartParams;
  onParamsChange?: Dispatch<SetStateAction<ChartParams>>;
  height?: number;
  showControls?: boolean;
  forecastDays?: number;
  confidenceInterval?: boolean;
  organizationId?: string;
  timeRange?: '1h' | '24h' | '7d' | '30d';
  showConfidenceInterval?: boolean;
  deviceIds?: string[];
}

const ConsumptionForecast: React.FC<ForecastProps> = ({
  params: _params,
  onParamsChange: _onParamsChange,
  height: _height = 320,
  showControls: _showControls = true,
  forecastDays: _forecastDays = 7,
  confidenceInterval: _confidenceInterval = true,
  organizationId,
  timeRange = '7d',
  showConfidenceInterval = true,
  deviceIds
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('csv');

  // Fetch real data using custom hooks
  const { data: trendsData, isLoading: trendsLoading, error: trendsError } = useConsumptionTrends({
    timeRange,
    interval: 'hourly',
    deviceId: deviceIds?.[0]
  });

  const { data: forecastData, isLoading: forecastLoading, error: forecastError } = useForecastData({
    timeRange,
    interval: 'daily',
    deviceId: deviceIds?.[0],
    forecastDays: 7,
    confidenceInterval: showConfidenceInterval
  });

  // Process and combine the data
  const processedData: ProcessedData = useMemo(() => {
    const result: ProcessedData = {
      historical: [],
      forecast: [],
      confidenceUpper: [],
      confidenceLower: []
    };

    // Process historical trends data
    if (trendsData && Array.isArray(trendsData)) {
      result.historical = trendsData.map((point: ChartDataPoint) => ({
        timestamp: point.timestamp,
        value: point.value || 0
      }));
    }

    // Process forecast data - ForecastData is a single object, not an array
    if (forecastData) {
      // Generate forecast points based on the forecast data
      const now = new Date();
      const forecastDays = 7;
      
      for (let i = 1; i <= forecastDays; i++) {
        const timestamp = new Date(now.getTime() + (i * 24 * 60 * 60 * 1000)).toISOString();
        result.forecast.push({
          timestamp,
          value: forecastData.predicted_consumption || 0
        });

        if (showConfidenceInterval && forecastData.confidence_interval) {
          result.confidenceUpper?.push({
            timestamp,
            value: forecastData.confidence_interval.upper || 0
          });

          result.confidenceLower?.push({
            timestamp,
            value: forecastData.confidence_interval.lower || 0
          });
        }
      }
    }

    return result;
  }, [trendsData, forecastData, showConfidenceInterval]);

  // Chart data configuration
  const chartData = useMemo(() => {
    const datasets: any[] = [];

    // Historical data with error handling
    if (processedData.historical.length > 0) {
      datasets.push({
        label: 'Historical',
        data: processedData.historical.map(point => {
          const timestamp = new Date(point.timestamp);
          return {
            x: isNaN(timestamp.getTime()) ? Date.now() : timestamp.getTime(),
            y: typeof point.value === 'number' ? point.value : 0
          };
        }),
        borderColor: chartColors.primary.border,
        backgroundColor: chartColors.primary.background,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
      });
    }

    // Forecast data with error handling
    if (processedData.forecast.length > 0) {
      datasets.push({
        label: 'Forecast',
        data: processedData.forecast.map(point => {
          const timestamp = new Date(point.timestamp);
          return {
            x: isNaN(timestamp.getTime()) ? Date.now() : timestamp.getTime(),
            y: typeof point.value === 'number' ? point.value : 0
          };
        }),
        borderColor: chartColors.energy.border,
        backgroundColor: chartColors.energy.background,
        borderDash: [5, 5],
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 5,
      });
    }

    // Confidence interval - upper bound
    if (showConfidenceInterval && processedData.confidenceUpper && processedData.confidenceUpper.length > 0) {
      datasets.push({
        label: 'Upper Confidence',
        data: processedData.confidenceUpper.map(point => {
          const timestamp = new Date(point.timestamp);
          return {
            x: isNaN(timestamp.getTime()) ? Date.now() : timestamp.getTime(),
            y: typeof point.value === 'number' ? point.value : 0
          };
        }),
        borderColor: 'rgba(255, 193, 7, 0.3)',
        backgroundColor: 'rgba(255, 193, 7, 0.1)',
        fill: '+1',
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 0,
        borderWidth: 1,
      });
    }

    // Confidence interval - lower bound
    if (showConfidenceInterval && processedData.confidenceLower && processedData.confidenceLower.length > 0) {
      datasets.push({
        label: 'Lower Confidence',
        data: processedData.confidenceLower.map(point => {
          const timestamp = new Date(point.timestamp);
          return {
            x: isNaN(timestamp.getTime()) ? Date.now() : timestamp.getTime(),
            y: typeof point.value === 'number' ? point.value : 0
          };
        }),
        borderColor: 'rgba(255, 193, 7, 0.3)',
        backgroundColor: 'rgba(255, 193, 7, 0.1)',
        fill: false,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 0,
        borderWidth: 1,
      });
    }

    return {
      datasets
    };
  }, [processedData, showConfidenceInterval]);

  const chartOptions = useMemo(() => ({
    ...defaultChartOptions,
    plugins: {
      ...defaultChartOptions.plugins,
      title: {
        display: true,
        text: 'Energy Consumption Forecast',
        font: {
          size: 16,
          weight: 'bold' as const
        }
      },
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          filter: (legendItem: any) => {
            // Hide confidence interval labels for cleaner legend
            return !legendItem.text.includes('Confidence');
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            hour: 'MMM dd HH:mm',
            day: 'MMM dd',
            week: 'MMM dd',
            month: 'MMM yyyy'
          }
        },
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Energy Consumption (kWh)'
        },
        beginAtZero: true
      }
    },
    interaction: {
      intersect: false,
      mode: 'index' as const
    }
  }), []);

  // Export functionality
  const handleExport = async () => {
    setIsExporting(true);
    try {
      const dataToExport = {
        historical: processedData.historical,
        forecast: processedData.forecast,
        ...(showConfidenceInterval && {
          confidenceUpper: processedData.confidenceUpper,
          confidenceLower: processedData.confidenceLower
        }),
        metadata: {
          exportedAt: new Date().toISOString(),
          timeRange,
          organizationId,
          deviceIds
        }
      };

      if (exportFormat === 'csv') {
        // Convert to CSV format
        const csvData = [
          ['Timestamp', 'Type', 'Value'],
          ...processedData.historical.map(item => [item.timestamp, 'Historical', item.value]),
          ...processedData.forecast.map(item => [item.timestamp, 'Forecast', item.value])
        ];
        
        const csvContent = csvData.map(row => row.join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `consumption-forecast-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        // Export as JSON
        const jsonContent = JSON.stringify(dataToExport, null, 2);
        const blob = new Blob([jsonContent], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `consumption-forecast-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  // Calculate summary statistics
  const stats = useMemo(() => {
    const currentAvg = processedData.historical.length > 0 
      ? processedData.historical.reduce((sum, point) => sum + point.value, 0) / processedData.historical.length 
      : 0;
    
    const forecastAvg = processedData.forecast.length > 0 
      ? processedData.forecast.reduce((sum, point) => sum + point.value, 0) / processedData.forecast.length 
      : 0;
    
    const projectedChange = currentAvg > 0 ? ((forecastAvg - currentAvg) / currentAvg) * 100 : 0;

    return {
      currentAvg: Math.round(currentAvg * 100) / 100,
      forecastAvg: Math.round(forecastAvg * 100) / 100,
      projectedChange: Math.round(projectedChange * 100) / 100,
      totalDataPoints: processedData.historical.length + processedData.forecast.length
    };
  }, [processedData]);

  if (trendsLoading || forecastLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="text-gray-600">Loading forecast data...</span>
          </div>
        </div>
      </div>
    );
  }

  if (trendsError || forecastError) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to Load Data</h3>
            <p className="text-gray-600">
              {String(trendsError || forecastError || 'Unable to load forecast data. Please try again.')}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (stats.totalDataPoints === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
            <p className="text-gray-600">
              No consumption data available for the selected time range.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-2">
          <TrendingUp className="h-6 w-6 text-blue-600" />
          <h3 className="text-xl font-semibold text-gray-900">Consumption Forecast</h3>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as 'csv' | 'json')}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm"
          >
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
          </select>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            <span>{isExporting ? 'Exporting...' : 'Export'}</span>
          </button>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500">Current Average</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatAnalyticsValue(stats.currentAvg, 'energy')}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500">Forecast Average</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatAnalyticsValue(stats.forecastAvg, 'energy')}
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500">Projected Change</div>
          <div className={`text-2xl font-bold ${stats.projectedChange > 0 ? 'text-red-600' : stats.projectedChange < 0 ? 'text-green-600' : 'text-gray-900'}`}>
            {stats.projectedChange > 0 ? '+' : ''}{stats.projectedChange}%
          </div>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500">Data Points</div>
          <div className="text-2xl font-bold text-gray-900">
            {stats.totalDataPoints.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="h-96">
        <Line 
          key={`forecast-chart-${organizationId}-${timeRange}-${Date.now()}`}
          data={chartData} 
          options={chartOptions} 
        />
      </div>

      {/* Legend and Notes */}
      <div className="mt-4 text-sm text-gray-600">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-1 bg-blue-600"></div>
            <span>Historical Data</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-1 border-t-2 border-dashed border-green-600"></div>
            <span>Forecast</span>
          </div>
          {showConfidenceInterval && (
            <div className="flex items-center space-x-2">
              <div className="w-4 h-1 bg-yellow-200"></div>
              <span>Confidence Interval</span>
            </div>
          )}
        </div>
        <p className="mt-2">
          Forecast is based on historical consumption patterns and may vary based on external factors.
          {showConfidenceInterval && ' Confidence intervals show the range of likely outcomes.'}
        </p>
      </div>
    </div>
  );
};

export default ConsumptionForecast;
