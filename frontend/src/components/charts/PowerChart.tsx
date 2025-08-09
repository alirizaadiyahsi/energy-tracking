import React from 'react';
import { Line } from 'react-chartjs-2';
import { ChartDataPoint } from '../../types';
import { defaultChartOptions, chartColors } from '../../utils/chartConfig';

interface PowerChartProps {
  data: ChartDataPoint[];
  isLoading?: boolean;
}

const PowerChart: React.FC<PowerChartProps> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-secondary-500">
        <p>No power data available</p>
      </div>
    );
  }

  const chartData = {
    labels: data.map(point => point.label || new Date(point.timestamp).toLocaleDateString()),
    datasets: [
      {
        label: 'Power Usage (W)',
        data: data.map(point => point.value),
        borderColor: chartColors.power.border,
        backgroundColor: chartColors.power.background,
        fill: true,
        tension: 0.4,
      },
    ],
  };

  const options = {
    ...defaultChartOptions,
    scales: {
      ...defaultChartOptions.scales,
      y: {
        ...defaultChartOptions.scales?.y,
        title: {
          display: true,
          text: 'Power (W)',
          color: '#6B7280',
        },
      },
    },
    plugins: {
      ...defaultChartOptions.plugins,
      tooltip: {
        ...defaultChartOptions.plugins?.tooltip,
        callbacks: {
          label: (context: any) => `Power: ${context.parsed.y.toFixed(1)} W`,
        },
      },
    },
  };

  return (
    <div className="h-64 w-full">
      <Line data={chartData} options={options} />
    </div>
  );
};

export default PowerChart;
