import React, { useState, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  Download, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle,
  MoreVertical,
  Eye,
  Settings,
  Activity
} from 'lucide-react';
import { formatAnalyticsValue } from '../../utils/analyticsTransformers';

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
  performance_trend: 'up' | 'down' | 'stable';
  alerts_count: number;
}

interface DevicePerformanceTableProps {
  maxDevices?: number;
  showFilters?: boolean;
  showActions?: boolean;
  compactMode?: boolean;
}

interface TableFiltersProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  statusFilter: string;
  onStatusFilterChange: (status: string) => void;
  typeFilter: string;
  onTypeFilterChange: (type: string) => void;
  sortBy: string;
  onSortByChange: (sort: string) => void;
  sortOrder: 'asc' | 'desc';
  onSortOrderChange: (order: 'asc' | 'desc') => void;
}

const TableFilters: React.FC<TableFiltersProps> = ({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  typeFilter,
  onTypeFilterChange,
  sortBy,
  onSortByChange,
  sortOrder,
  onSortOrderChange,
}) => {
  const statusOptions = [
    { value: 'all', label: 'All Status' },
    { value: 'online', label: 'Online' },
    { value: 'offline', label: 'Offline' },
    { value: 'maintenance', label: 'Maintenance' },
    { value: 'warning', label: 'Warning' },
  ];

  const typeOptions = [
    { value: 'all', label: 'All Types' },
    { value: 'hvac', label: 'HVAC' },
    { value: 'lighting', label: 'Lighting' },
    { value: 'motor', label: 'Motor' },
    { value: 'compressor', label: 'Compressor' },
    { value: 'sensor', label: 'Sensor' },
  ];

  const sortOptions = [
    { value: 'device_name', label: 'Device Name' },
    { value: 'efficiency', label: 'Efficiency' },
    { value: 'energy_consumption', label: 'Energy Consumption' },
    { value: 'power_usage', label: 'Power Usage' },
    { value: 'uptime_percentage', label: 'Uptime' },
    { value: 'anomaly_score', label: 'Anomaly Score' },
  ];

  return (
    <div className="flex flex-wrap items-center gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
      {/* Search */}
      <div className="flex-1 min-w-64">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search devices..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-2">
        <Filter className="h-4 w-4 text-gray-500" />
        <select
          value={statusFilter}
          onChange={(e) => onStatusFilterChange(e.target.value)}
          className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {statusOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={typeFilter}
          onChange={(e) => onTypeFilterChange(e.target.value)}
          className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {typeOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Sort */}
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-600">Sort by:</span>
        <select
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value)}
          className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {sortOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <button
          onClick={() => onSortOrderChange(sortOrder === 'asc' ? 'desc' : 'asc')}
          className="p-1 hover:bg-gray-200 rounded"
          title={`Sort ${sortOrder === 'asc' ? 'Descending' : 'Ascending'}`}
        >
          {sortOrder === 'asc' ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
};

interface DeviceRowProps {
  device: DevicePerformance;
  showActions: boolean;
  compactMode: boolean;
  onDeviceClick: (device: DevicePerformance) => void;
  onViewDetails: (device: DevicePerformance) => void;
  onConfigure: (device: DevicePerformance) => void;
}

const DeviceRow: React.FC<DeviceRowProps> = ({
  device,
  showActions,
  compactMode,
  onDeviceClick,
  onViewDetails,
  onConfigure,
}) => {
  const [showActionsMenu, setShowActionsMenu] = useState(false);

  const getStatusIcon = () => {
    switch (device.status) {
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'offline':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      case 'maintenance':
        return <Settings className="h-4 w-4 text-orange-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (device.status) {
      case 'online':
        return 'text-green-700 bg-green-100';
      case 'offline':
        return 'text-red-700 bg-red-100';
      case 'maintenance':
        return 'text-orange-700 bg-orange-100';
      case 'warning':
        return 'text-yellow-700 bg-yellow-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  const getEfficiencyColor = () => {
    if (device.efficiency >= 90) return 'text-green-600';
    if (device.efficiency >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrendIcon = () => {
    switch (device.performance_trend) {
      case 'up':
        return <TrendingUp className="h-3 w-3 text-green-500" />;
      case 'down':
        return <TrendingDown className="h-3 w-3 text-red-500" />;
      default:
        return <div className="h-3 w-3 bg-gray-400 rounded-full" />;
    }
  };

  return (
    <tr 
      className="hover:bg-gray-50 cursor-pointer border-b border-gray-200"
      onClick={() => onDeviceClick(device)}
    >
      {/* Device Info */}
      <td className="px-4 py-3">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <div className="font-medium text-gray-900">{device.device_name}</div>
            {!compactMode && (
              <div className="text-sm text-gray-500">{device.device_id}</div>
            )}
          </div>
        </div>
      </td>

      {/* Type & Location */}
      <td className="px-4 py-3">
        <div>
          <div className="text-sm font-medium text-gray-900 capitalize">{device.device_type}</div>
          {!compactMode && (
            <div className="text-sm text-gray-500">{device.location}</div>
          )}
        </div>
      </td>

      {/* Status */}
      <td className="px-4 py-3">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor()}`}>
          {device.status}
        </span>
      </td>

      {/* Efficiency */}
      <td className="px-4 py-3">
        <div className="flex items-center space-x-2">
          <span className={`font-medium ${getEfficiencyColor()}`}>
            {device.efficiency.toFixed(1)}%
          </span>
          {getTrendIcon()}
        </div>
      </td>

      {/* Energy & Power */}
      <td className="px-4 py-3">
        <div>
          <div className="text-sm font-medium text-gray-900">
            {formatAnalyticsValue(device.energy_consumption, 'energy')}
          </div>
          {!compactMode && (
            <div className="text-sm text-gray-500">
              {formatAnalyticsValue(device.power_usage, 'power')}
            </div>
          )}
        </div>
      </td>

      {/* Uptime */}
      <td className="px-4 py-3">
        <div className="flex items-center space-x-2">
          <div className="flex-1 bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full ${device.uptime_percentage >= 95 ? 'bg-green-500' : device.uptime_percentage >= 85 ? 'bg-yellow-500' : 'bg-red-500'}`}
              style={{ width: `${device.uptime_percentage}%` }}
            />
          </div>
          <span className="text-sm font-medium text-gray-700 min-w-12">
            {device.uptime_percentage.toFixed(1)}%
          </span>
        </div>
      </td>

      {/* Alerts */}
      <td className="px-4 py-3">
        {device.alerts_count > 0 ? (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
            {device.alerts_count}
          </span>
        ) : (
          <span className="text-sm text-gray-400">None</span>
        )}
      </td>

      {/* Cost */}
      {!compactMode && (
        <td className="px-4 py-3">
          <div className="text-sm font-medium text-gray-900">
            ${device.cost_per_hour.toFixed(2)}/hr
          </div>
        </td>
      )}

      {/* Actions */}
      {showActions && (
        <td className="px-4 py-3">
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowActionsMenu(!showActionsMenu);
              }}
              className="p-1 hover:bg-gray-200 rounded"
            >
              <MoreVertical className="h-4 w-4 text-gray-400" />
            </button>
            
            {showActionsMenu && (
              <div className="absolute right-0 top-8 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewDetails(device);
                    setShowActionsMenu(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                >
                  <Eye className="h-4 w-4" />
                  <span>View Details</span>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onConfigure(device);
                    setShowActionsMenu(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                >
                  <Settings className="h-4 w-4" />
                  <span>Configure</span>
                </button>
              </div>
            )}
          </div>
        </td>
      )}
    </tr>
  );
};

const DevicePerformanceTable: React.FC<DevicePerformanceTableProps> = ({
  maxDevices = 50,
  showFilters = true,
  showActions = true,
  compactMode = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('device_name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  // Mock device data
  const mockDevices: DevicePerformance[] = useMemo(() => [
    {
      device_id: 'dev_001',
      device_name: 'HVAC Unit A1',
      device_type: 'hvac',
      location: 'Building A, Floor 1',
      status: 'online',
      efficiency: 87.5,
      energy_consumption: 45.2,
      power_usage: 3.8,
      uptime_percentage: 98.5,
      last_maintenance: '2024-07-15',
      next_maintenance: '2024-10-15',
      cost_per_hour: 4.52,
      anomaly_score: 15.3,
      performance_trend: 'stable',
      alerts_count: 0,
    },
    {
      device_id: 'dev_002',
      device_name: 'LED Lighting System B',
      device_type: 'lighting',
      location: 'Building B, All Floors',
      status: 'online',
      efficiency: 94.2,
      energy_consumption: 12.8,
      power_usage: 1.2,
      uptime_percentage: 99.8,
      last_maintenance: '2024-08-01',
      next_maintenance: '2025-02-01',
      cost_per_hour: 1.28,
      anomaly_score: 8.1,
      performance_trend: 'up',
      alerts_count: 0,
    },
    {
      device_id: 'dev_003',
      device_name: 'Compressor Motor C3',
      device_type: 'compressor',
      location: 'Basement, Mechanical Room',
      status: 'warning',
      efficiency: 68.7,
      energy_consumption: 78.5,
      power_usage: 6.5,
      uptime_percentage: 89.2,
      last_maintenance: '2024-05-20',
      next_maintenance: '2024-08-20',
      cost_per_hour: 7.85,
      anomaly_score: 75.8,
      performance_trend: 'down',
      alerts_count: 3,
    },
    {
      device_id: 'dev_004',
      device_name: 'Ventilation Fan D1',
      device_type: 'hvac',
      location: 'Building D, Roof',
      status: 'maintenance',
      efficiency: 0,
      energy_consumption: 0,
      power_usage: 0,
      uptime_percentage: 0,
      last_maintenance: '2024-08-09',
      next_maintenance: '2024-11-09',
      cost_per_hour: 0,
      anomaly_score: 0,
      performance_trend: 'stable',
      alerts_count: 1,
    },
    {
      device_id: 'dev_005',
      device_name: 'Water Heater E2',
      device_type: 'motor',
      location: 'Building E, Utility Room',
      status: 'online',
      efficiency: 82.1,
      energy_consumption: 32.4,
      power_usage: 2.7,
      uptime_percentage: 95.7,
      last_maintenance: '2024-06-30',
      next_maintenance: '2024-12-30',
      cost_per_hour: 3.24,
      anomaly_score: 22.5,
      performance_trend: 'stable',
      alerts_count: 0,
    },
    {
      device_id: 'dev_006',
      device_name: 'Temperature Sensor F1',
      device_type: 'sensor',
      location: 'Building F, Multiple Zones',
      status: 'offline',
      efficiency: 0,
      energy_consumption: 0.1,
      power_usage: 0.01,
      uptime_percentage: 0,
      last_maintenance: '2024-07-01',
      next_maintenance: '2025-01-01',
      cost_per_hour: 0.01,
      anomaly_score: 95.2,
      performance_trend: 'down',
      alerts_count: 2,
    },
  ], []);

  // Filter and sort devices
  const filteredDevices = useMemo(() => {
    let filtered = mockDevices.filter(device => {
      const matchesSearch = device.device_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           device.device_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           device.location.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || device.status === statusFilter;
      const matchesType = typeFilter === 'all' || device.device_type === typeFilter;
      
      return matchesSearch && matchesStatus && matchesType;
    });

    // Sort devices
    filtered.sort((a, b) => {
      const aValue = a[sortBy as keyof DevicePerformance];
      const bValue = b[sortBy as keyof DevicePerformance];
      
      let comparison = 0;
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        comparison = aValue.localeCompare(bValue);
      } else if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered.slice(0, maxDevices);
  }, [mockDevices, searchTerm, statusFilter, typeFilter, sortBy, sortOrder, maxDevices]);

  const handleExport = () => {
    const csvContent = [
      [
        'Device ID', 'Device Name', 'Type', 'Location', 'Status', 'Efficiency (%)', 
        'Energy Consumption (kWh)', 'Power Usage (kW)', 'Uptime (%)', 
        'Cost per Hour ($)', 'Anomaly Score', 'Performance Trend', 'Alerts Count'
      ],
      ...filteredDevices.map(device => [
        device.device_id,
        device.device_name,
        device.device_type,
        device.location,
        device.status,
        device.efficiency.toFixed(1),
        device.energy_consumption.toFixed(1),
        device.power_usage.toFixed(1),
        device.uptime_percentage.toFixed(1),
        device.cost_per_hour.toFixed(2),
        device.anomaly_score.toFixed(1),
        device.performance_trend,
        device.alerts_count.toString()
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `device-performance-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDeviceClick = (device: DevicePerformance) => {
    console.log('Device clicked:', device);
    // Could navigate to device detail page or open modal
  };

  const handleViewDetails = (device: DevicePerformance) => {
    console.log('View details for:', device);
    // Could open detailed modal or navigate to detail page
  };

  const handleConfigure = (device: DevicePerformance) => {
    console.log('Configure device:', device);
    // Could open configuration modal
  };

  const summary = useMemo(() => {
    const total = filteredDevices.length;
    const online = filteredDevices.filter(d => d.status === 'online').length;
    const avgEfficiency = filteredDevices.reduce((sum, d) => sum + d.efficiency, 0) / total;
    const totalAlerts = filteredDevices.reduce((sum, d) => sum + d.alerts_count, 0);
    
    return { total, online, avgEfficiency, totalAlerts };
  }, [filteredDevices]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Device Performance</h3>
        </div>
        <button
          onClick={handleExport}
          className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <Download className="h-4 w-4" />
          <span>Export</span>
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-3 bg-blue-50 rounded-lg">
        <div className="text-center">
          <p className="text-xs text-blue-600 font-medium">Total Devices</p>
          <p className="text-sm font-semibold text-blue-900">{summary.total}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-blue-600 font-medium">Online</p>
          <p className="text-sm font-semibold text-blue-900">{summary.online}/{summary.total}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-blue-600 font-medium">Avg Efficiency</p>
          <p className="text-sm font-semibold text-blue-900">{summary.avgEfficiency.toFixed(1)}%</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-blue-600 font-medium">Total Alerts</p>
          <p className="text-sm font-semibold text-blue-900">{summary.totalAlerts}</p>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <TableFilters
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          typeFilter={typeFilter}
          onTypeFilterChange={setTypeFilter}
          sortBy={sortBy}
          onSortByChange={setSortBy}
          sortOrder={sortOrder}
          onSortOrderChange={setSortOrder}
        />
      )}

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Device
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type & Location
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Efficiency
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Energy Usage
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Uptime
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Alerts
                </th>
                {!compactMode && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost
                  </th>
                )}
                {showActions && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredDevices.length > 0 ? (
                filteredDevices.map((device) => (
                  <DeviceRow
                    key={device.device_id}
                    device={device}
                    showActions={showActions}
                    compactMode={compactMode}
                    onDeviceClick={handleDeviceClick}
                    onViewDetails={handleViewDetails}
                    onConfigure={handleConfigure}
                  />
                ))
              ) : (
                <tr>
                  <td colSpan={compactMode ? 7 : showActions ? 9 : 8} className="px-4 py-8 text-center text-gray-500">
                    No devices found matching your criteria
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-sm text-gray-600">
        <span>Showing {filteredDevices.length} of {mockDevices.length} devices</span>
        <span>Last updated: {new Date().toLocaleString()}</span>
      </div>
    </div>
  );
};

export default DevicePerformanceTable;
