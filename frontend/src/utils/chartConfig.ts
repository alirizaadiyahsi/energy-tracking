import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Default chart options
export const defaultChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#fff',
      bodyColor: '#fff',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1,
    },
  },
  scales: {
    x: {
      grid: {
        display: false,
      },
      ticks: {
        color: '#6B7280',
      },
    },
    y: {
      grid: {
        color: 'rgba(107, 114, 128, 0.1)',
      },
      ticks: {
        color: '#6B7280',
      },
    },
  },
  elements: {
    line: {
      tension: 0.4,
    },
    point: {
      radius: 4,
      hoverRadius: 6,
    },
  },
};

// Chart color schemes
export const chartColors = {
  power: {
    background: 'rgba(139, 69, 19, 0.1)',
    border: 'rgb(139, 69, 19)',
    fill: 'rgba(139, 69, 19, 0.1)',
  },
  energy: {
    background: 'rgba(34, 197, 94, 0.1)',
    border: 'rgb(34, 197, 94)',
    fill: 'rgba(34, 197, 94, 0.1)',
  },
  primary: {
    background: 'rgba(59, 130, 246, 0.1)',
    border: 'rgb(59, 130, 246)',
    fill: 'rgba(59, 130, 246, 0.1)',
  },
};
