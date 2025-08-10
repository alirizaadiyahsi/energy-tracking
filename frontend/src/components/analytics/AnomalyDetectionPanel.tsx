import React, { useState, useMemo } from 'react';
import { AlertTriangle, CheckCircle, Info, Bell, Clock, MapPin } from 'lucide-react';
import { useAlerts } from '../../hooks/useAnalyticsData';
import { formatAnalyticsValue } from '../../utils/analyticsTransformers';

interface AnomalyDetectionPanelProps {
  maxAlerts?: number;
  showResolvedAlerts?: boolean;
  autoRefresh?: boolean;
}

interface AnomalyCardProps {
  id: string;
  title: string;
  description: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
  location?: string;
  deviceName?: string;
  value?: number;
  threshold?: number;
  status: 'active' | 'acknowledged' | 'resolved';
  onAcknowledge?: (id: string) => void;
  onResolve?: (id: string) => void;
}

const AnomalyCard: React.FC<AnomalyCardProps> = ({
  id,
  title,
  description,
  severity,
  timestamp,
  location,
  deviceName,
  value,
  threshold,
  status,
  onAcknowledge,
  onResolve,
}) => {
  const getSeverityIcon = () => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const getSeverityColor = () => {
    switch (severity) {
      case 'critical':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'info':
        return 'border-blue-200 bg-blue-50';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'active':
        return 'bg-red-100 text-red-800';
      case 'acknowledged':
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else {
      return `${diffDays}d ago`;
    }
  };

  return (
    <div className={`p-4 rounded-lg border ${getSeverityColor()} ${status === 'resolved' ? 'opacity-75' : ''}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          {getSeverityIcon()}
          <h4 className="font-medium text-gray-900">{title}</h4>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${getStatusColor()}`}>
            {status}
          </span>
          <span className="text-xs text-gray-500 flex items-center">
            <Clock className="h-3 w-3 mr-1" />
            {formatTimestamp(timestamp)}
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-sm text-gray-600 mb-3">{description}</p>

      {/* Details */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3 text-xs">
        {deviceName && (
          <div>
            <span className="text-gray-500">Device:</span>
            <p className="font-medium">{deviceName}</p>
          </div>
        )}
        {location && (
          <div>
            <span className="text-gray-500 flex items-center">
              <MapPin className="h-3 w-3 mr-1" />
              Location:
            </span>
            <p className="font-medium">{location}</p>
          </div>
        )}
        {value !== undefined && (
          <div>
            <span className="text-gray-500">Current Value:</span>
            <p className="font-medium text-red-600">
              {formatAnalyticsValue(value, 'power')}
            </p>
          </div>
        )}
        {threshold !== undefined && (
          <div>
            <span className="text-gray-500">Threshold:</span>
            <p className="font-medium">{formatAnalyticsValue(threshold, 'power')}</p>
          </div>
        )}
      </div>

      {/* Actions */}
      {status === 'active' && (
        <div className="flex space-x-2">
          {onAcknowledge && (
            <button
              onClick={() => onAcknowledge(id)}
              className="px-3 py-1 text-xs bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
            >
              Acknowledge
            </button>
          )}
          {onResolve && (
            <button
              onClick={() => onResolve(id)}
              className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
            >
              Resolve
            </button>
          )}
        </div>
      )}
    </div>
  );
};

interface AnomalySummaryProps {
  alertsData: any;
}

const AnomalySummary: React.FC<AnomalySummaryProps> = ({ alertsData }) => {
  const stats = useMemo(() => {
    if (!alertsData?.alerts) {
      return {
        total: 0,
        critical: 0,
        warning: 0,
        info: 0,
        resolved: 0,
        active: 0,
      };
    }

    const alerts = alertsData.alerts;
    return {
      total: alerts.length,
      critical: alerts.filter((a: any) => a.severity === 'critical').length,
      warning: alerts.filter((a: any) => a.severity === 'warning').length,
      info: alerts.filter((a: any) => a.severity === 'info').length,
      resolved: alerts.filter((a: any) => a.status === 'resolved').length,
      active: alerts.filter((a: any) => a.status === 'active').length,
    };
  }, [alertsData]);

  return (
    <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
      <div className="text-center">
        <p className="text-lg font-bold text-gray-900">{stats.total}</p>
        <p className="text-xs text-gray-500">Total Alerts</p>
      </div>
      <div className="text-center">
        <p className="text-lg font-bold text-red-600">{stats.critical}</p>
        <p className="text-xs text-gray-500">Critical</p>
      </div>
      <div className="text-center">
        <p className="text-lg font-bold text-yellow-600">{stats.warning}</p>
        <p className="text-xs text-gray-500">Warning</p>
      </div>
      <div className="text-center">
        <p className="text-lg font-bold text-blue-600">{stats.info}</p>
        <p className="text-xs text-gray-500">Info</p>
      </div>
      <div className="text-center">
        <p className="text-lg font-bold text-red-600">{stats.active}</p>
        <p className="text-xs text-gray-500">Active</p>
      </div>
      <div className="text-center">
        <p className="text-lg font-bold text-green-600">{stats.resolved}</p>
        <p className="text-xs text-gray-500">Resolved</p>
      </div>
    </div>
  );
};

const AnomalyDetectionPanel: React.FC<AnomalyDetectionPanelProps> = ({
  maxAlerts = 10,
  showResolvedAlerts = false,
  autoRefresh = true,
}) => {
  const [filterSeverity, setFilterSeverity] = useState<'all' | 'critical' | 'warning' | 'info'>('all');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'acknowledged' | 'resolved'>('all');

  const { data: alertsData, isLoading, error, refetch } = useAlerts(maxAlerts);

  // Generate mock alerts for demonstration
  const mockAlerts = useMemo(() => [
    {
      id: '1',
      title: 'High Power Consumption Detected',
      description: 'HVAC system is consuming 40% more power than normal operating levels.',
      severity: 'critical' as const,
      timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(), // 15 minutes ago
      location: 'Building A - Floor 2',
      deviceName: 'HVAC Unit 01',
      value: 3400,
      threshold: 2500,
      status: 'active' as const,
    },
    {
      id: '2',
      title: 'Unusual Energy Pattern',
      description: 'Lighting system showing unexpected energy spikes during off-hours.',
      severity: 'warning' as const,
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
      location: 'Building B - Floor 1',
      deviceName: 'Lighting Panel 03',
      value: 850,
      threshold: 600,
      status: 'acknowledged' as const,
    },
    {
      id: '3',
      title: 'Equipment Efficiency Drop',
      description: 'Motor efficiency has decreased by 15% over the past week.',
      severity: 'warning' as const,
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
      location: 'Production Floor',
      deviceName: 'Motor Controller 05',
      value: 72.5,
      threshold: 85,
      status: 'active' as const,
    },
    {
      id: '4',
      title: 'Power Factor Correction Needed',
      description: 'Power factor has dropped below acceptable levels.',
      severity: 'info' as const,
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), // 6 hours ago
      location: 'Main Electrical Panel',
      deviceName: 'PFC Unit 01',
      status: 'resolved' as const,
    },
    {
      id: '5',
      title: 'Scheduled Maintenance Due',
      description: 'Equipment maintenance window approaching based on usage patterns.',
      severity: 'info' as const,
      timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(), // 12 hours ago
      location: 'Building C',
      deviceName: 'Chiller Unit 02',
      status: 'active' as const,
    },
  ], []);

  const alerts = alertsData?.alerts || mockAlerts;

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert: any) => {
      const severityMatch = filterSeverity === 'all' || alert.severity === filterSeverity;
      const statusMatch = filterStatus === 'all' || alert.status === filterStatus;
      const resolvedMatch = showResolvedAlerts || alert.status !== 'resolved';
      return severityMatch && statusMatch && resolvedMatch;
    });
  }, [alerts, filterSeverity, filterStatus, showResolvedAlerts]);

  const handleAcknowledge = (alertId: string) => {
    console.log(`Acknowledging alert: ${alertId}`);
    // TODO: Implement alert acknowledgment
  };

  const handleResolve = (alertId: string) => {
    console.log(`Resolving alert: ${alertId}`);
    // TODO: Implement alert resolution
  };

  const handleRefresh = () => {
    refetch();
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-16 bg-gray-200 rounded-lg mb-4"></div>
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg mb-4"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <p className="text-red-600 font-medium">Failed to load anomaly detection data</p>
        </div>
        <p className="text-red-500 text-sm mt-1">{error.message}</p>
        <button
          onClick={handleRefresh}
          className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-2">
          <Bell className="h-5 w-5 text-orange-500" />
          <h3 className="text-lg font-semibold text-gray-900">Anomaly Detection & Alerts</h3>
          {autoRefresh && (
            <div className="flex items-center space-x-1 text-xs text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Live</span>
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center space-x-2">
          {/* Severity Filter */}
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value as any)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-orange-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>

          {/* Status Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-orange-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>

          <button
            onClick={handleRefresh}
            className="px-3 py-1 text-sm bg-orange-600 text-white rounded hover:bg-orange-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Statistics */}
      <AnomalySummary alertsData={{ alerts }} />

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-3" />
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Anomalies Detected</h4>
            <p className="text-gray-500">Your energy systems are operating within normal parameters.</p>
          </div>
        ) : (
          filteredAlerts.map((alert: any) => (
            <AnomalyCard
              key={alert.id}
              {...alert}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
            />
          ))
        )}
      </div>

      {filteredAlerts.length > 0 && filteredAlerts.length >= maxAlerts && (
        <div className="text-center py-4">
          <p className="text-sm text-gray-500">
            Showing {filteredAlerts.length} of {alerts.length} alerts
          </p>
          <button className="mt-2 text-sm text-orange-600 hover:text-orange-700 font-medium">
            View All Alerts
          </button>
        </div>
      )}
    </div>
  );
};

export default AnomalyDetectionPanel;
