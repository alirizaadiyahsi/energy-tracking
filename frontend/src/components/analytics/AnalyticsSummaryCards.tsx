import React from 'react';
import { Activity, Zap, TrendingUp, AlertTriangle, Target, DollarSign, BarChart3, Gauge } from 'lucide-react';
import { AnalyticsSummary } from '../../types/analytics';
import { formatAnalyticsValue, calculatePercentageChange } from '../../utils/analyticsTransformers';
import MetricCard from './MetricCard';

interface AnalyticsSummaryCardsProps {
  data?: AnalyticsSummary;
  isLoading?: boolean;
  onCardClick?: (metric: string) => void;
}

const AnalyticsSummaryCards: React.FC<AnalyticsSummaryCardsProps> = ({
  data,
  isLoading = false,
  onCardClick,
}) => {
  // Sample previous period data for trend calculation
  // In a real app, this would come from the API or be calculated from historical data
  const previousPeriodData = {
    total_energy_consumption: data ? data.total_energy_consumption * 0.95 : 0,
    average_power: data ? data.average_power * 1.02 : 0,
    system_efficiency: data ? data.system_efficiency * 0.98 : 0,
    total_cost: data ? data.total_cost * 1.05 : 0,
    active_devices: data ? data.active_devices - 1 : 0,
    anomalies_detected: data ? data.anomalies_detected + 2 : 0,
    peak_demand: data ? data.peak_demand * 0.97 : 0,
    energy_savings: data ? data.energy_savings * 0.85 : 0,
  };

  const metrics = [
    {
      key: 'energy_consumption',
      title: 'Total Energy Consumption',
      value: data ? formatAnalyticsValue(data.total_energy_consumption, 'energy') : 'N/A',
      trend: data ? calculatePercentageChange(data.total_energy_consumption, previousPeriodData.total_energy_consumption) : undefined,
      icon: BarChart3,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      key: 'average_power',
      title: 'Average Power',
      value: data ? formatAnalyticsValue(data.average_power, 'power') : 'N/A',
      trend: data ? calculatePercentageChange(data.average_power, previousPeriodData.average_power) : undefined,
      icon: Zap,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
    {
      key: 'system_efficiency',
      title: 'System Efficiency',
      value: data ? formatAnalyticsValue(data.system_efficiency, 'percentage') : 'N/A',
      trend: data ? calculatePercentageChange(data.system_efficiency, previousPeriodData.system_efficiency) : undefined,
      icon: Gauge,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      key: 'total_cost',
      title: 'Total Cost',
      value: data ? formatAnalyticsValue(data.total_cost, 'currency') : 'N/A',
      trend: data ? calculatePercentageChange(data.total_cost, previousPeriodData.total_cost) : undefined,
      icon: DollarSign,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      key: 'active_devices',
      title: 'Active Devices',
      value: data ? formatAnalyticsValue(data.active_devices, 'count') : 'N/A',
      trend: data ? calculatePercentageChange(data.active_devices, previousPeriodData.active_devices) : undefined,
      icon: Activity,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100',
    },
    {
      key: 'anomalies_detected',
      title: 'Anomalies Detected',
      value: data ? formatAnalyticsValue(data.anomalies_detected, 'count') : 'N/A',
      trend: data ? calculatePercentageChange(data.anomalies_detected, previousPeriodData.anomalies_detected) : undefined,
      icon: AlertTriangle,
      color: 'text-red-600',
      bgColor: 'bg-red-100',
    },
    {
      key: 'peak_demand',
      title: 'Peak Demand',
      value: data ? formatAnalyticsValue(data.peak_demand, 'power') : 'N/A',
      trend: data ? calculatePercentageChange(data.peak_demand, previousPeriodData.peak_demand) : undefined,
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
    {
      key: 'energy_savings',
      title: 'Energy Savings',
      value: data ? formatAnalyticsValue(data.energy_savings, 'currency') : 'N/A',
      trend: data ? calculatePercentageChange(data.energy_savings, previousPeriodData.energy_savings) : undefined,
      icon: Target,
      color: 'text-teal-600',
      bgColor: 'bg-teal-100',
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <MetricCard
          key={metric.key}
          title={metric.title}
          value={metric.value}
          trend={metric.trend}
          icon={metric.icon}
          color={metric.color}
          bgColor={metric.bgColor}
          onClick={onCardClick ? () => onCardClick(metric.key) : undefined}
          isLoading={isLoading}
        />
      ))}
    </div>
  );
};

export default AnalyticsSummaryCards;
