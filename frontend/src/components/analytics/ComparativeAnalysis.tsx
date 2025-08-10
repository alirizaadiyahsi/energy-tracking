import React, { useState, useMemo } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import { Download, TrendingUp, Calendar, BarChart3, ArrowUpDown } from 'lucide-react';
import { ChartDataPoint } from '../../types';
import { ChartParams } from '../../types/analytics';
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
  onParamsChange?: (params: ChartParams) => void;
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
      id: 'this_week',
      label: 'This Week',
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date().toISOString(),
      color: '#3b82f6',
    },
    {
      id: 'last_week',
      label: 'Last Week',
      start: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      color: '#10b981',
    },
    {
      id: 'this_month',
      label: 'This Month',
      start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString(),
      end: new Date().toISOString(),
      color: '#f59e0b',
    },
    {
      id: 'last_month',
      label: 'Last Month',
      start: new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1).toISOString(),
      end: new Date(new Date().getFullYear(), new Date().getMonth(), 0).toISOString(),
      color: '#ef4444',
    },
  ];

  const handlePeriodToggle = (period: ComparisonPeriod) => {
    const exists = selectedPeriods.find(p => p.id === period.id);
    if (exists) {
      onPeriodsChange(selectedPeriods.filter(p => p.id !== period.id));
    } else if (selectedPeriods.length < 4) {
      onPeriodsChange([...selectedPeriods, period]);
    }
  };

  return (
    <div className="space-y-4 mb-6">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center space-x-2">
          <ArrowUpDown className="h-4 w-4 text-blue-500" />
          <select
            value={comparisonType}
            onChange={(e) => onComparisonTypeChange(e.target.value as typeof comparisonType)}
            disabled={isLoading}
            className="text-sm border border-blue-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {comparisonTypes.map(type => (
              <option key={type.value} value={type.value}>
                Compare {type.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <BarChart3 className="h-4 w-4 text-blue-500" />
          <select
            value={chartType}
            onChange={(e) => onChartTypeChange(e.target.value as typeof chartType)}
            disabled={isLoading}
            className="text-sm border border-blue-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="bar">Bar Chart</option>
            <option value="line">Line Chart</option>
          </select>
        </div>
      </div>

      {comparisonType === 'period' && (
        <div>
          <p className="text-sm text-gray-600 mb-2">Select periods to compare (max 4):</p>
          <div className="flex flex-wrap gap-2">
            {predefinedPeriods.map(period => {
              const isSelected = selectedPeriods.find(p => p.id === period.id);
              return (
                <button
                  key={period.id}
                  onClick={() => handlePeriodToggle(period)}
                  disabled={isLoading || (!isSelected && selectedPeriods.length >= 4)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                    isSelected
                      ? 'bg-blue-100 border-blue-300 text-blue-700'
                      : 'bg-gray-50 border-gray-300 text-gray-600 hover:bg-gray-100'
                  } ${
                    !isSelected && selectedPeriods.length >= 4
                      ? 'opacity-50 cursor-not-allowed'
                      : 'cursor-pointer'
                  }`}
                  style={isSelected ? { borderColor: period.color, color: period.color } : {}}
                >
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

interface ComparisonStatsProps {
  data: any[];
  selectedPeriods: ComparisonPeriod[];
}

const ComparisonStats: React.FC<ComparisonStatsProps> = ({ data, selectedPeriods }) => {
  const stats = useMemo(() => {
    if (!data || data.length === 0 || selectedPeriods.length === 0) {
      return [];
    }

    return selectedPeriods.map(period => {
      const periodData = data.find(d => d.periodId === period.id);
      if (!periodData) return null;

      const total = periodData.data.reduce((sum: number, point: ChartDataPoint) => sum + point.value, 0);
      const average = total / periodData.data.length;
      const peak = Math.max(...periodData.data.map((point: ChartDataPoint) => point.value));

      return {
        period,
        total,
        average,
        peak,
        dataPoints: periodData.data.length,
      };
    }).filter((stat): stat is NonNullable<typeof stat> => stat !== null);
  }, [data, selectedPeriods]);

  if (stats.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4 p-3 bg-blue-50 rounded-lg">
      {stats.map((stat) => (
        <div key={stat.period.id} className="text-center">
          <div className="flex items-center justify-center space-x-2 mb-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: stat.period.color }}
            />
            <p className="text-xs font-medium text-blue-900">{stat.period.label}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-blue-600">Total</p>
            <p className="text-sm font-semibold text-blue-900">
              {formatAnalyticsValue(stat.total, 'energy')}
            </p>
            <p className="text-xs text-blue-600">Avg: {formatAnalyticsValue(stat.average, 'energy')}</p>
            <p className="text-xs text-blue-600">Peak: {formatAnalyticsValue(stat.peak, 'energy')}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

const ComparativeAnalysis: React.FC<ComparativeAnalysisProps> = ({
  height = 400,
  showControls = true,
}) => {
  const [selectedPeriods, setSelectedPeriods] = useState<ComparisonPeriod[]>([
    {
      id: 'this_week',
      label: 'This Week',
      start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date().toISOString(),
      color: '#3b82f6',
    },
    {
      id: 'last_week',
      label: 'Last Week',
      start: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString(),
      end: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      color: '#10b981',
    },
  ]);

  const [comparisonType, setComparisonType] = useState<'period' | 'device' | 'metric'>('period');
  const [chartType, setChartType] = useState<'bar' | 'line'>('bar');

  // Mock data generation for comparison
  const mockData = useMemo(() => {
    if (selectedPeriods.length === 0) return [];

    return selectedPeriods.map(period => {
      const dataPoints: ChartDataPoint[] = [];
      const startDate = new Date(period.start);
      const endDate = new Date(period.end);
      const daysDiff = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
      
      const pointsCount = Math.min(daysDiff, 14); // Max 14 points for readability
      const intervalMs = (endDate.getTime() - startDate.getTime()) / pointsCount;

      for (let i = 0; i < pointsCount; i++) {
        const timestamp = new Date(startDate.getTime() + (i * intervalMs)).toISOString();
        
        // Generate realistic data with period-specific characteristics
        let baseValue = 25;
        if (period.id.includes('week')) {
          baseValue = 20 + Math.sin(i * 0.3) * 8; // Weekly pattern
        } else if (period.id.includes('month')) {
          baseValue = 30 + Math.sin(i * 0.1) * 10; // Monthly pattern
        }
        
        const seasonalVariation = Math.sin(i * 0.5) * 3;
        const randomNoise = (Math.random() - 0.5) * 4;
        const value = Math.max(0, baseValue + seasonalVariation + randomNoise);

        dataPoints.push({
          timestamp,
          value: Math.round(value * 100) / 100,
        });
      }

      return {
        periodId: period.id,
        label: period.label,
        data: dataPoints,
        color: period.color,
      };
    });
  }, [selectedPeriods]);

  const handleExport = () => {
    const csvContent = [
      ['Timestamp', ...selectedPeriods.map(p => `${p.label} (kWh)`)],
      ...mockData[0]?.data.map((_, index) => [
        new Date(mockData[0].data[index].timestamp).toLocaleDateString(),
        ...mockData.map(dataset => dataset.data[index]?.value?.toString() || '0')
      ]) || []
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `comparative-analysis-${comparisonType}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Prepare chart data
  const chartData = useMemo(() => {
    if (mockData.length === 0) return { labels: [], datasets: [] };

    const labels = mockData[0]?.data.map(point => 
      new Date(point.timestamp).toLocaleDateString()
    ) || [];

    const datasets = mockData.map(dataset => ({
      label: dataset.label,
      data: dataset.data.map(point => point.value),
      backgroundColor: chartType === 'bar' ? `${dataset.color}66` : 'transparent',
      borderColor: dataset.color,
      borderWidth: 2,
      fill: chartType === 'line' ? false : true,
      tension: chartType === 'line' ? 0.4 : 0,
      pointRadius: chartType === 'line' ? 3 : 0,
    }));

    return { labels, datasets };
  }, [mockData, chartType]);

  const chartOptions = {
    ...defaultChartOptions,
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    scales: {
      ...defaultChartOptions.scales,
      y: {
        ...defaultChartOptions.scales?.y,
        title: {
          display: true,
          text: 'Energy Consumption (kWh)',
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
          text: 'Time Period',
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
        display: true,
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
            const label = context.dataset.label || '';
            const value = formatAnalyticsValue(context.parsed.y, 'energy');
            return `${label}: ${value}`;
          },
        },
      },
    },
  };

  if (selectedPeriods.length === 0) {
    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">Comparative Analysis</h3>
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
            isLoading={false}
          />
        )}

        <div style={{ height: `${height}px` }} className="flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <div className="text-center">
            <Calendar className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-500 mb-1">No periods selected for comparison</p>
            <p className="text-xs text-gray-400">Select at least one period to start comparing</p>
          </div>
        </div>
      </div>
    );
  }

  const ChartComponent = chartType === 'bar' ? Bar : Line;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <TrendingUp className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Comparative Analysis</h3>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Download className="h-4 w-4" />
          <span>Export</span>
        </button>
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
          isLoading={false}
        />
      )}

      {/* Statistics */}
      <ComparisonStats 
        data={mockData}
        selectedPeriods={selectedPeriods}
      />

      {/* Chart */}
      <div style={{ height: `${height}px` }} className="w-full">
        <ChartComponent 
          key={`comparative-chart-${chartType}-${selectedPeriods.length}-${selectedPeriods.map(p => p.id).join('-')}`}
          data={chartData} 
          options={chartOptions} 
        />
      </div>
    </div>
  );
};

export default ComparativeAnalysis;
