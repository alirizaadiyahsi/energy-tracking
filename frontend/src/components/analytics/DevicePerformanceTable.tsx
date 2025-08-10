import React, { useState, useMemo, useEffect } from 'react';
import { 
  Search, 
  Download, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle,
  Eye,
  Settings,
  Activity
} from 'lucide-react';
import { formatAnalyticsValue } from '../../utils/analyticsTransformers';
import deviceService from '../../services/deviceService';

interface DevicePerformance {
  device_id: string;
  device_name: string;
  device_type: string;
  location: string;
  status: 'online' | 'offline' | 'maintenance' | 'warning';
  efficiency: number;
  energy_consumption: number;
  power_usage: number;
  uptime_percentage: number;
  last_maintenance: string;
  next_maintenance: string;
  cost_per_hour: number;
  anomaly_score: number;
  performance_trend: 'improving' | 'stable' | 'declining';
  alerts_count: number;
  firmware_version?: string;
  model?: string;
  installed_date?: string;
}

interface DevicePerformanceTableProps {
  maxDevices?: number;
  showFilters?: boolean;
  showExport?: boolean;
}

const DevicePerformanceTable: React.FC<DevicePerformanceTableProps> = ({
  maxDevices = 20,
  showFilters = true,
  showExport = true,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState('device_name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const [devicesData, setDevicesData] = useState<any[]>([]);
  const [devicesLoading, setDevicesLoading] = useState(true);
  const [devicesError, setDevicesError] = useState<string | null>(null);

  // Fetch devices data
  useEffect(() => {
    const fetchDevices = async () => {
      try {
        setDevicesLoading(true);
        const data = await deviceService.getDevices();
        setDevicesData(data || []);
        setDevicesError(null);
      } catch (error) {
        console.error('Error fetching devices:', error);
        setDevicesError('Failed to load devices');
        setDevicesData([]);
      } finally {
        setDevicesLoading(false);
      }
    };

    fetchDevices();
  }, []);

  // Transform real device data to performance data format
  const performanceDevices: DevicePerformance[] = useMemo(() => {
    if (!devicesData || !Array.isArray(devicesData)) return [];
    
    return devicesData.map((device: any) => {
      // Calculate efficiency based on power vs base_power
      const efficiency = device.base_power > 0 
        ? Math.min(100, (device.power / device.base_power) * 100)
        : 85; // Default efficiency if no base_power

      // Calculate performance trend based on recent data (simplified)
      const performanceTrend = efficiency > 90 ? 'improving' 
        : efficiency < 70 ? 'declining' 
        : 'stable';

      return {
        device_id: device.id || `dev_${device.name?.toLowerCase().replace(/\s+/g, '_') || 'unknown'}`,
        device_name: device.name || 'Unknown Device',
        device_type: device.type || 'unknown',
        location: device.location || 'Unknown Location',
        status: device.status || 'offline',
        efficiency: Math.round(efficiency * 10) / 10,
        energy_consumption: device.energy || 0,
        power_usage: device.power || 0,
        uptime_percentage: device.status === 'online' ? 98.5 : device.status === 'offline' ? 0 : 85.2,
        last_maintenance: device.last_maintenance || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        next_maintenance: device.next_maintenance || new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        cost_per_hour: ((device.power || 0) * 0.15) / 1000, // $0.15 per kWh
        anomaly_score: 0, // Would come from analytics service anomaly detection
        performance_trend: performanceTrend as 'improving' | 'stable' | 'declining',
        alerts_count: 0, // Would come from alerts service
        firmware_version: device.firmware_version || '1.0.0',
        model: device.model || 'Unknown Model',
        installed_date: device.created_at?.split('T')[0] || '2024-01-01',
      } as DevicePerformance;
    });
  }, [devicesData]);

  // Filter and sort devices
  const filteredDevices = useMemo(() => {
    if (devicesLoading || !performanceDevices) return [];
    
    let filtered = performanceDevices.filter(device => {
      const matchesSearch = device.device_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           device.device_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           device.location.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || device.status === statusFilter;
      const matchesType = typeFilter === 'all' || device.device_type === typeFilter;
      
      return matchesSearch && matchesStatus && matchesType;
    });

    // Sort devices
    filtered.sort((a, b) => {
      let aValue: any = a[sortBy as keyof DevicePerformance];
      let bValue: any = b[sortBy as keyof DevicePerformance];
      
      if (typeof aValue === 'string') aValue = aValue.toLowerCase();
      if (typeof bValue === 'string') bValue = bValue.toLowerCase();
      
      // Handle undefined values
      if (aValue === undefined && bValue === undefined) return 0;
      if (aValue === undefined) return sortOrder === 'asc' ? 1 : -1;
      if (bValue === undefined) return sortOrder === 'asc' ? -1 : 1;
      
      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered.slice(0, maxDevices);
  }, [performanceDevices, searchTerm, statusFilter, typeFilter, sortBy, sortOrder, maxDevices]);

  // Loading state
  if (devicesLoading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-secondary-900">Device Performance</h3>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <span className="ml-2 text-secondary-600">Loading device data...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (devicesError) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-secondary-900">Device Performance</h3>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-secondary-600 mb-2">Failed to load device data</p>
            <p className="text-sm text-secondary-500">Please check your connection and try again.</p>
          </div>
        </div>
      </div>
    );
  }

  // No data state
  if (!performanceDevices || performanceDevices.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-medium text-secondary-900">Device Performance</h3>
        </div>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-secondary-600 mb-2">No devices found</p>
            <p className="text-sm text-secondary-500">Add devices to start monitoring performance.</p>
          </div>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      online: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      offline: { color: 'bg-red-100 text-red-800', icon: AlertTriangle },
      maintenance: { color: 'bg-yellow-100 text-yellow-800', icon: Settings },
      warning: { color: 'bg-orange-100 text-orange-800', icon: AlertTriangle },
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.offline;
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'declining':
        return <TrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <div className="w-4 h-4 bg-gray-300 rounded-full" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-medium text-secondary-900">Device Performance</h3>
          <p className="text-sm text-secondary-600">Real-time monitoring of device efficiency and performance</p>
        </div>
        {showExport && (
          <button className="btn-secondary">
            <Download className="w-4 h-4 mr-2" />
            Export
          </button>
        )}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search devices..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 w-full"
            />
          </div>
          
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="all">All Status</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
            <option value="maintenance">Maintenance</option>
            <option value="warning">Warning</option>
          </select>
          
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="all">All Types</option>
            <option value="hvac">HVAC</option>
            <option value="lighting">Lighting</option>
            <option value="motor">Motor</option>
            <option value="compressor">Compressor</option>
          </select>
          
          <select
            value={`${sortBy}_${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('_');
              setSortBy(field);
              setSortOrder(order as 'asc' | 'desc');
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="device_name_asc">Name (A-Z)</option>
            <option value="device_name_desc">Name (Z-A)</option>
            <option value="efficiency_desc">Efficiency (High-Low)</option>
            <option value="efficiency_asc">Efficiency (Low-High)</option>
            <option value="power_usage_desc">Power (High-Low)</option>
            <option value="power_usage_asc">Power (Low-High)</option>
          </select>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Efficiency</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Power</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Energy</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Trend</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Alerts</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredDevices.map((device) => (
              <tr key={device.device_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{device.device_name}</div>
                    <div className="text-sm text-gray-500">{device.location}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getStatusBadge(device.status)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{device.efficiency.toFixed(1)}%</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{formatAnalyticsValue(device.power_usage, 'power')}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{formatAnalyticsValue(device.energy_consumption, 'energy')}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {getTrendIcon(device.performance_trend)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {device.alerts_count > 0 ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      {device.alerts_count}
                    </span>
                  ) : (
                    <span className="text-sm text-gray-500">None</span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button className="text-primary-600 hover:text-primary-900">
                    <Eye className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="mt-6 flex items-center justify-between">
        <span className="text-sm text-gray-700">
          Showing {filteredDevices.length} of {performanceDevices.length} devices
        </span>
      </div>
    </div>
  );
};

export default DevicePerformanceTable;
