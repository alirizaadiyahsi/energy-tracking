import React from 'react';
import { Line } from 'react-chartjs-2';
import { ChartDataPoint } from '../../types';
import { defaultChartOptions, chartColors } from '../../utils/chartConfig';

interface EnergyChartProps {
  data: ChartDataPoint[];
  isLoading?: boolean;
}

const EnergyChart: React.FC<EnergyChartProps> = ({ data, isLoading }) => {
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
        <p>No energy data available</p>
      </div>
    );
  }

  const chartData = {
    labels: data.map(point => point.label || new Date(point.timestamp).toLocaleDateString()),
    datasets: [
      {
        label: 'Energy Consumption (kWh)',
        data: data.map(point => point.value),
        borderColor: chartColors.energy.border,
        backgroundColor: chartColors.energy.background,
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
          text: 'Energy (kWh)',
          color: '#6B7280',
        },
      },
    },
    plugins: {
      ...defaultChartOptions.plugins,
      tooltip: {
        ...defaultChartOptions.plugins?.tooltip,
        callbacks: {
          label: (context: any) => `Energy: ${context.parsed.y.toFixed(2)} kWh`,
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

export default EnergyChart;
