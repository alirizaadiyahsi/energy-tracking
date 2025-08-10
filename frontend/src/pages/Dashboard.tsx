import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { Activity, Zap, TrendingUp, AlertTriangle } from 'lucide-react';
import dashboardService from '../services/dashboardService';
import deviceService from '../services/deviceService';
import { formatPower, formatEnergy } from '../utils';
import PowerChart from '../components/charts/PowerChart';
import EnergyChart from '../components/charts/EnergyChart';
import TimeIntervalSelector, { TimeIntervalOption, timeIntervals } from '../components/TimeIntervalSelector';

const Dashboard: React.FC = () => {
  // State for time interval selection
  const [selectedInterval, setSelectedInterval] = useState<TimeIntervalOption>(timeIntervals[1]); // Default to hourly 24h

  const { data: dashboardData, isLoading, error } = useQuery(
    'dashboard',
    () => dashboardService.getDashboardData(),
    {
      refetchInterval: 5000, // Refresh every 5 seconds for real-time updates
    }
  );

  // Fetch device data to get accurate device counts
  const { data: devices } = useQuery(
    'dashboard-devices',
    () => deviceService.getDevices(),
    {
      refetchInterval: 5000, // Refresh every 5 seconds for real-time updates
    }
  );

  const { data: powerChartData, isLoading: powerLoading } = useQuery(
    ['powerChart', selectedInterval.interval, selectedInterval.timeRange],
    () => {
      console.log('Fetching power data with:', selectedInterval.interval, selectedInterval.timeRange);
      return dashboardService.getPowerChart({
        interval: selectedInterval.interval,
        timeRange: selectedInterval.timeRange
      });
    },
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  const { data: energyChartData, isLoading: energyLoading } = useQuery(
    ['energyChart', selectedInterval.interval, selectedInterval.timeRange],
    () => {
      console.log('Fetching energy data with:', selectedInterval.interval, selectedInterval.timeRange);
      return dashboardService.getEnergyChart({
        interval: selectedInterval.interval,
        timeRange: selectedInterval.timeRange
      });
    },
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 p-8">
        <p>Failed to load dashboard data</p>
      </div>
    );
  }

  const stats = [
    {
      name: 'Total Devices',
      value: devices?.length || 0,
      icon: Activity,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Online Devices',
      value: devices?.filter(device => device.status === 'online').length || 0,
      icon: Zap,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Energy Today',
      value: formatEnergy(dashboardData?.totalEnergyToday || 0),
      icon: TrendingUp,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
    },
    {
      name: 'Average Power',
      value: formatPower(dashboardData?.averagePower || 0),
      icon: Activity,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
  ];

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-secondary-900">Dashboard</h1>
          <p className="mt-2 text-sm text-secondary-700">
            Overview of your energy tracking system
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-8">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <div key={stat.name} className="card">
                <div className="flex items-center">
                  <div className={`flex-shrink-0 p-3 rounded-lg ${stat.bgColor}`}>
                    <Icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-secondary-600">{stat.name}</p>
                    <p className="text-2xl font-semibold text-secondary-900">{stat.value}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Alerts */}
      {dashboardData?.alerts && dashboardData.alerts.length > 0 && (
        <div className="mt-8">
          <div className="card">
            <div className="flex items-center mb-4">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
              <h2 className="text-lg font-medium text-secondary-900">Recent Alerts</h2>
            </div>
            <div className="space-y-3">
              {dashboardData.alerts.slice(0, 5).map((alert) => (
                <div
                  key={alert.id}
                  className={`p-3 rounded-lg ${
                    alert.type === 'error'
                      ? 'bg-red-50 border border-red-200'
                      : alert.type === 'warning'
                      ? 'bg-yellow-50 border border-yellow-200'
                      : 'bg-blue-50 border border-blue-200'
                  }`}
                >
                  <div className="flex items-start">
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-secondary-900">{alert.title}</h4>
                      <p className="text-sm text-secondary-600 mt-1">{alert.message}</p>
                    </div>
                    <div className="text-xs text-secondary-500">
                      {new Date(alert.createdAt).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-secondary-900">Analytics</h2>
          <TimeIntervalSelector
            selectedInterval={selectedInterval}
            onIntervalChange={setSelectedInterval}
          />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="card">
            <h3 className="text-lg font-medium text-secondary-900 mb-4">Power Usage</h3>
            <PowerChart data={powerChartData || []} isLoading={powerLoading} />
          </div>
          <div className="card">
            <h3 className="text-lg font-medium text-secondary-900 mb-4">Energy Consumption</h3>
            <EnergyChart data={energyChartData || []} isLoading={energyLoading} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
