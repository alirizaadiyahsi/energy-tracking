// Analytics-specific types for the frontend
export interface ChartParams {
  interval: 'minutely' | 'hourly' | 'daily';
  timeRange: '1h' | '24h' | '7d' | '30d';
  deviceId?: string;
}

export interface EfficiencyAnalysis {
  overall_efficiency: number;
  device_efficiency: DeviceEfficiency[];
  improvement_suggestions: string[];
}

export interface DeviceEfficiency {
  device_id: string;
  efficiency: number;
  device_name?: string;
}

export interface AlertSummary {
  total_alerts: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  recent_trends: string;
}

export interface Alert {
  id: string;
  title: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  severity: 'critical' | 'high' | 'medium' | 'low';
  device_id?: string;
  device_name?: string;
  timestamp: string;
  is_read: boolean;
  anomaly_score?: number;
}

export interface AlertsResponse {
  alerts: Alert[];
  summary: AlertSummary;
}

export interface ForecastData {
  forecast_period: string;
  predicted_consumption: number;
  confidence_interval: {
    lower: number;
    upper: number;
  };
  forecast_accuracy: number;
  methodology?: string;
  generated_at?: string;
}

export interface EnergyReport {
  report_id: string;
  period: string;
  devices: string[];
  total_consumption: number;
  total_cost: number;
  generated_at: string;
  summary_stats?: {
    avg_daily_consumption: number;
    peak_demand: number;
    efficiency_score: number;
  };
}

export interface ReportRequest {
  start_date: string;
  end_date: string;
  device_ids?: string[];
  include_charts?: boolean;
  format?: 'json' | 'pdf' | 'csv';
}

export interface ComparisonPeriod {
  label: string;
  start_date: string;
  end_date: string;
}

export interface ComparisonResult {
  current_period: ComparisonPeriod;
  previous_period: ComparisonPeriod;
  metrics: {
    energy_consumption: {
      current: number;
      previous: number;
      change_percentage: number;
      change_absolute: number;
    };
    average_power: {
      current: number;
      previous: number;
      change_percentage: number;
      change_absolute: number;
    };
    efficiency: {
      current: number;
      previous: number;
      change_percentage: number;
      change_absolute: number;
    };
    cost: {
      current: number;
      previous: number;
      change_percentage: number;
      change_absolute: number;
    };
  };
}

export interface AnalyticsSummary {
  total_energy_consumption: number;
  average_power: number;
  system_efficiency: number;
  total_cost: number;
  active_devices: number;
  anomalies_detected: number;
  peak_demand: number;
  energy_savings: number;
  trend_indicators: {
    energy_trend: 'up' | 'down' | 'stable';
    efficiency_trend: 'up' | 'down' | 'stable';
    cost_trend: 'up' | 'down' | 'stable';
  };
}
