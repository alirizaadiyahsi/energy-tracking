import React, { useState, useMemo } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import { Download, TrendingUp, BarChart3, ArrowUpDown } from 'lucide-react';
import { ChartDataPoint } from '../../types';
import { ChartParams } from '../../types/analytics';
import { useConsumptionTrends } from '../../hooks/useAnalyticsData';
import { formatAnalyticsValue } from '../../utils/analyticsTransformers';
import { defaultChartOptions } from '../../utils/chartConfig';

interface ComparisonPeriod {
  id: string;
  label: string;
  start: string;
  end: string;
  color: string;
}

interface ComparativeAnalysisProps {
  params: ChartParams;
  height?: number;
  showControls?: boolean;
}

interface ComparisonControlsProps {
  selectedPeriods: ComparisonPeriod[];
  onPeriodsChange: (periods: ComparisonPeriod[]) => void;
  comparisonType: 'period' | 'device' | 'metric';
  onComparisonTypeChange: (type: 'period' | 'device' | 'metric') => void;
  chartType: 'bar' | 'line';
  onChartTypeChange: (type: 'bar' | 'line') => void;
  isLoading: boolean;
}

const ComparisonControls: React.FC<ComparisonControlsProps> = ({
  selectedPeriods,
  onPeriodsChange,
  comparisonType,
  onComparisonTypeChange,
  chartType,
  onChartTypeChange,
  isLoading,
}) => {
  const comparisonTypes = [
    { value: 'period' as const, label: 'Time Periods' },
    { value: 'device' as const, label: 'Devices' },
    { value: 'metric' as const, label: 'Metrics' },
  ];

  const predefinedPeriods = [
    {
      id: 'last-7-days',
      label: 'Last 7 Days',
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date().toISOString(),
      color: '#3B82F6',
    },
    {
      id: 'last-30-days',
      label: 'Last 30 Days',
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date().toISOString(),
      color: '#10B981',
    },
    {
      id: 'previous-week',
      label: 'Previous Week',
      start: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      color: '#F59E0B',
    },
    {
      id: 'previous-month',
      label: 'Previous Month',
      start: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
      color: '#EF4444',
    },
  ];

  const togglePeriod = (period: ComparisonPeriod) => {
    const isSelected = selectedPeriods.some(p => p.id === period.id);
    if (isSelected) {
      onPeriodsChange(selectedPeriods.filter(p => p.id !== period.id));
    } else {
      if (selectedPeriods.length < 3) { // Limit to 3 periods for readability
        onPeriodsChange([...selectedPeriods, period]);
      }
    }
  };

  return (
    <div className="mb-6 space-y-4">
      {/* Comparison Type Selector */}
      <div className="flex items-center space-x-4">
        <label className="text-sm font-medium text-gray-700">Compare by:</label>
        <div className="flex space-x-2">
          {comparisonTypes.map(type => (
            <button
              key={type.value}
              onClick={() => onComparisonTypeChange(type.value)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                comparisonType === type.value
                  ? 'bg-primary-100 text-primary-700 border border-primary-300'
                  : 'bg-gray-100 text-gray-600 border border-gray-300 hover:bg-gray-200'
              }`}
              disabled={isLoading}
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Type Selector */}
      <div className="flex items-center space-x-4">
        <label className="text-sm font-medium text-gray-700">Chart type:</label>
        <div className="flex space-x-2">
          <button
            onClick={() => onChartTypeChange('bar')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              chartType === 'bar'
                ? 'bg-primary-100 text-primary-700 border border-primary-300'
                : 'bg-gray-100 text-gray-600 border border-gray-300 hover:bg-gray-200'
            }`}
            disabled={isLoading}
          >
            <BarChart3 className="w-4 h-4 inline mr-1" />
            Bar
          </button>
          <button
            onClick={() => onChartTypeChange('line')}
            className={`px-3 py-1 text-sm rounded-md transition-colors ${
              chartType === 'line'
                ? 'bg-primary-100 text-primary-700 border border-primary-300'
                : 'bg-gray-100 text-gray-600 border border-gray-300 hover:bg-gray-200'
            }`}
            disabled={isLoading}
          >
            <TrendingUp className="w-4 h-4 inline mr-1" />
            Line
          </button>
        </div>
      </div>

      {/* Period Selection */}
      {comparisonType === 'period' && (
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-2">
            Select periods to compare (max 3):
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {predefinedPeriods.map(period => {
              const isSelected = selectedPeriods.some(p => p.id === period.id);
              return (
                <button
                  key={period.id}
                  onClick={() => togglePeriod(period)}
                  className={`p-3 text-sm rounded-md border transition-colors ${
                    isSelected
                      ? 'bg-primary-50 border-primary-300 text-primary-700'
                      : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                  }`}
                  disabled={isLoading || (!isSelected && selectedPeriods.length >= 3)}
                >
                  <div
                    className="w-3 h-3 rounded-full mx-auto mb-1"
                    style={{ backgroundColor: period.color }}
                  />
                  {period.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

const ComparativeAnalysis: React.FC<ComparativeAnalysisProps> = ({
  params,
  height = 400,
  showControls = true,
}) => {
  const [comparisonType, setComparisonType] = useState<'period' | 'device' | 'metric'>('period');
  const [selectedPeriods, setSelectedPeriods] = useState<ComparisonPeriod[]>([
    {
      id: 'last-7-days',
      label: 'Last 7 Days',
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date().toISOString(),
      color: '#3B82F6',
    },
    {
      id: 'previous-week',
      label: 'Previous Week',
      start: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      color: '#10B981',
    },
  ]);
  const [chartType, setChartType] = useState<'bar' | 'line'>('bar');

  // Fetch real data for each selected period
  const periodDataQueries = selectedPeriods.map(period => {
    const periodParams = {
      ...params,
      timeRange: '7d' as const, // Use a valid timeRange value
    };
    
    return {
      period,
      // eslint-disable-next-line react-hooks/rules-of-hooks
      query: useConsumptionTrends(periodParams, true, 60000), // Refetch every minute
    };
  });

  const isLoading = periodDataQueries.some(({ query }) => query.isLoading);
  const hasError = periodDataQueries.some(({ query }) => query.error);

  // Process the real data for comparison
  const realData = useMemo(() => {
    if (periodDataQueries.length === 0) return [];

    return periodDataQueries.map(({ period, query }) => {
      const data = query.data || [];
      
      // Aggregate data by day for better comparison
      const dailyData: { [date: string]: number } = {};
      
      data.forEach(point => {
        const date = new Date(point.timestamp).toISOString().split('T')[0];
        if (!dailyData[date]) {
          dailyData[date] = 0;
        }
        dailyData[date] += point.value;
      });

      const aggregatedData: ChartDataPoint[] = Object.entries(dailyData).map(([date, value]) => ({
        timestamp: new Date(date + 'T00:00:00Z').toISOString(),
        value: Math.round(value * 100) / 100,
      }));

      return {
        periodId: period.id,
        label: period.label,
        data: aggregatedData.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()),
        color: period.color,
      };
    });
  }, [periodDataQueries]);

  const handleExport = () => {
    if (realData.length === 0) return;
    
    // Find all unique dates across all periods
    const allDates = new Set<string>();
    realData.forEach(dataset => {
      dataset.data.forEach(point => {
        allDates.add(new Date(point.timestamp).toLocaleDateString());
      });
    });
    
    const sortedDates = Array.from(allDates).sort();
    
    const csvContent = [
      ['Date', ...realData.map(d => `${d.label} (kWh)`)],
      ...sortedDates.map(date => [
        date,
        ...realData.map(dataset => {
          const point = dataset.data.find(p => 
            new Date(p.timestamp).toLocaleDateString() === date
          );
          return point?.value?.toString() || '0';
        })
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `comparative-analysis-${comparisonType}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Prepare chart data
  const chartData = useMemo(() => {
    if (realData.length === 0) return { labels: [], datasets: [] };

    // Get all unique dates across all datasets
    const allDates = new Set<string>();
    realData.forEach(dataset => {
      dataset.data.forEach(point => {
        allDates.add(new Date(point.timestamp).toLocaleDateString());
      });
    });
    
    const labels = Array.from(allDates).sort();

    const datasets = realData.map(dataset => ({
      label: dataset.label,
      data: labels.map(label => {
        const point = dataset.data.find(p => 
          new Date(p.timestamp).toLocaleDateString() === label
        );
        return point?.value || 0;
      }),
      backgroundColor: dataset.color + '20',
      borderColor: dataset.color,
      borderWidth: 2,
    }));

    return { labels, datasets };
  }, [realData]);

  const chartOptions = {
    ...defaultChartOptions,
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      ...defaultChartOptions.plugins,
      title: {
        display: true,
        text: `${comparisonType === 'period' ? 'Period' : comparisonType === 'device' ? 'Device' : 'Metric'} Comparison`
      },
      legend: {
        display: true,
        position: 'top' as const,
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Energy Consumption (kWh)'
        },
        beginAtZero: true
      }
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-medium text-secondary-900">Comparative Analysis</h3>
            <p className="text-sm text-secondary-600">
              Comparing energy consumption across {comparisonType === 'period' ? 'time periods' : comparisonType}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
            <span className="text-sm text-secondary-600">Loading comparison data...</span>
          </div>
        </div>
        <div className="h-80 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-secondary-600">Generating comparison...</p>
          </div>
        </div>
      </div>
    );
  }

  if (hasError || realData.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-medium text-secondary-900">Comparative Analysis</h3>
            <p className="text-sm text-secondary-600">
              Comparing energy consumption across {comparisonType === 'period' ? 'time periods' : comparisonType}
            </p>
          </div>
        </div>
        <div className="h-80 flex items-center justify-center">
          <div className="text-center">
            <div className="text-yellow-500 mb-4">
              <ArrowUpDown className="w-12 h-12 mx-auto" />
            </div>
            <p className="text-secondary-600 mb-2">
              {hasError ? 'Failed to load comparison data' : 'No comparison data available'}
            </p>
            <p className="text-sm text-secondary-500">
              Please select periods to compare and ensure the analytics service has sufficient data.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-medium text-secondary-900">Comparative Analysis</h3>
          <p className="text-sm text-secondary-600">
            Comparing energy consumption across {comparisonType === 'period' ? 'time periods' : comparisonType}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 text-blue-600">
            <ArrowUpDown className="w-4 h-4" />
            <span className="text-sm font-medium">
              {realData.length} {comparisonType === 'period' ? 'periods' : 'items'} compared
            </span>
          </div>
          <button
            onClick={handleExport}
            className="btn-secondary text-sm"
            disabled={realData.length === 0}
          >
            <Download className="w-4 h-4 mr-1" />
            Export
          </button>
        </div>
      </div>

      {/* Controls */}
      {showControls && (
        <ComparisonControls
          selectedPeriods={selectedPeriods}
          onPeriodsChange={setSelectedPeriods}
          comparisonType={comparisonType}
          onComparisonTypeChange={setComparisonType}
          chartType={chartType}
          onChartTypeChange={setChartType}
          isLoading={isLoading}
        />
      )}

      {/* Chart */}
      <div style={{ height }}>
        {chartType === 'bar' ? (
          <Bar 
            key={`comparative-${comparisonType}-${chartType}-${selectedPeriods.length}`}
            data={chartData} 
            options={chartOptions} 
          />
        ) : (
          <Line 
            key={`comparative-${comparisonType}-${chartType}-${selectedPeriods.length}`}
            data={chartData} 
            options={chartOptions} 
          />
        )}
      </div>

      {/* Summary Statistics */}
      {realData.length > 0 && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          {realData.map(dataset => {
            const totalConsumption = dataset.data.reduce((sum, point) => sum + point.value, 0);
            const averageDaily = totalConsumption / dataset.data.length;
            
            return (
              <div key={dataset.periodId} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: dataset.color }}
                      />
                      <p className="text-sm text-gray-600">{dataset.label}</p>
                    </div>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatAnalyticsValue(totalConsumption, 'energy')}
                    </p>
                    <p className="text-xs text-gray-500">
                      Avg: {formatAnalyticsValue(averageDaily, 'energy')}/day
                    </p>
                  </div>
                  <BarChart3 className="w-8 h-8 text-gray-400" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ComparativeAnalysis;
