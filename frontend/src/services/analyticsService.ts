import api from './api';
import { ApiResponse, ChartDataPoint } from '../types';
import {
  ChartParams,
  EfficiencyAnalysis,
  AlertsResponse,
  ForecastData,
  EnergyReport,
  ReportRequest,
  ComparisonResult,
  AnalyticsSummary
} from '../types/analytics';

class AnalyticsService {
  // Cache for storing frequently accessed data
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Get data from cache if available and not expired
   */
  private getFromCache<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data as T;
    }
    this.cache.delete(key);
    return null;
  }

  /**
   * Store data in cache
   */
  private setCache<T>(key: string, data: T, ttl: number = this.CACHE_TTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  /**
   * Clear cache for specific pattern or all cache
   */
  clearCache(pattern?: string): void {
    if (pattern) {
      const keysToDelete = Array.from(this.cache.keys()).filter(key => key.includes(pattern));
      keysToDelete.forEach(key => this.cache.delete(key));
    } else {
      this.cache.clear();
    }
  }

  /**
   * Get energy consumption trends
   */
  async getConsumptionTrends(params: ChartParams): Promise<ChartDataPoint[]> {
    const cacheKey = `consumption_trends_${JSON.stringify(params)}`;
    const cached = this.getFromCache<ChartDataPoint[]>(cacheKey);
    if (cached) return cached;

    try {
      const queryParams = new URLSearchParams({
        interval: params.interval,
        time_range: params.timeRange,
        ...(params.deviceId && { device_id: params.deviceId })
      });

      const response = await api.get<ApiResponse<ChartDataPoint[]>>(
        `/api/v1/analytics/consumption/trends?${queryParams}`
      );

      if (response.data.success && response.data.data) {
        this.setCache(cacheKey, response.data.data, 2 * 60 * 1000); // 2 minutes cache
        return response.data.data;
      }
      throw new Error(response.data.message || 'Failed to fetch consumption trends');
    } catch (error) {
      console.error('Error fetching consumption trends:', error);
      // Return empty array instead of mock data to indicate no data available
      return [];
    }
  }

  /**
   * Get power usage trends
   */
  async getPowerTrends(params: ChartParams): Promise<ChartDataPoint[]> {
    const cacheKey = `power_trends_${JSON.stringify(params)}`;
    const cached = this.getFromCache<ChartDataPoint[]>(cacheKey);
    if (cached) return cached;

    try {
      const queryParams = new URLSearchParams({
        interval: params.interval,
        time_range: params.timeRange,
        ...(params.deviceId && { device_id: params.deviceId })
      });

      const response = await api.get<ApiResponse<ChartDataPoint[]>>(
        `/api/v1/analytics/power/trends?${queryParams}`
      );

      if (response.data.success && response.data.data) {
        this.setCache(cacheKey, response.data.data, 2 * 60 * 1000); // 2 minutes cache
        return response.data.data;
      }
      throw new Error(response.data.message || 'Failed to fetch power trends');
    } catch (error) {
      console.error('Error fetching power trends:', error);
      // Return empty array instead of mock data to indicate no data available
      return [];
    }
  }

  /**
   * Get efficiency analysis
   */
  async getEfficiencyAnalysis(): Promise<EfficiencyAnalysis> {
    const cacheKey = 'efficiency_analysis';
    const cached = this.getFromCache<EfficiencyAnalysis>(cacheKey);
    if (cached) return cached;

    try {
      const response = await api.get<ApiResponse<EfficiencyAnalysis>>('/api/v1/analytics/efficiency/analysis');

      if (response.data.success && response.data.data) {
        this.setCache(cacheKey, response.data.data, 10 * 60 * 1000); // 10 minutes cache
        return response.data.data;
      }
      throw new Error(response.data.message || 'Failed to fetch efficiency analysis');
    } catch (error) {
      console.error('Error fetching efficiency analysis:', error);
      
      // Return empty efficiency data structure instead of mock data
      const emptyData: EfficiencyAnalysis = {
        overall_efficiency: 0,
        device_efficiency: [],
        improvement_suggestions: ['No efficiency data available - check device connections and analytics service'],
      };

      return emptyData;
    }
  }

  /**
   * Get anomaly alerts
   */
  async getAlerts(limit: number = 20): Promise<AlertsResponse> {
    const cacheKey = `alerts_${limit}`;
    const cached = this.getFromCache<AlertsResponse>(cacheKey);
    if (cached) return cached;

    try {
      const response = await api.get<ApiResponse<AlertsResponse>>(`/api/v1/analytics/alerts?limit=${limit}`);

      if (response.data.success && response.data.data) {
        this.setCache(cacheKey, response.data.data, 1 * 60 * 1000); // 1 minute cache for alerts
        return response.data.data;
      }
      throw new Error(response.data.message || 'Failed to fetch alerts');
    } catch (error) {
      console.error('Error fetching alerts:', error);
      
      // Return empty alerts structure instead of mock data
      const emptyAlerts: AlertsResponse = {
        alerts: [],
        summary: {
          total_alerts: 0,
          critical_count: 0,
          warning_count: 0,
          info_count: 0,
          recent_trends: 'No alert data available',
        },
      };
      
      return emptyAlerts;
    }
  }

  /**
   * Mark alert as read
   */
  async markAlertAsRead(alertId: string): Promise<void> {
    try {
      const response = await api.post<ApiResponse<{ alertId: string }>>(
        `/api/v1/analytics/alerts/${alertId}/mark-read`
      );

      if (!response.data.success) {
        throw new Error(response.data.message || 'Failed to mark alert as read');
      }

      // Clear alerts cache to refresh data
      this.clearCache('alerts_');
    } catch (error) {
      console.error('Error marking alert as read:', error);
      throw error;
    }
  }

  /**
   * Get consumption forecast
   */
  async getForecast(daysAhead: number = 30): Promise<ForecastData> {
    const cacheKey = `forecast_${daysAhead}`;
    const cached = this.getFromCache<ForecastData>(cacheKey);
    if (cached) return cached;

    try {
      const response = await api.get<ApiResponse<ForecastData>>(
        `/api/v1/analytics/forecasting?days_ahead=${daysAhead}`
      );

      if (response.data.success && response.data.data) {
        this.setCache(cacheKey, response.data.data, 30 * 60 * 1000); // 30 minutes cache
        return response.data.data;
      }
      throw new Error(response.data.message || 'Failed to fetch forecast');
    } catch (error) {
      console.error('Error fetching forecast:', error);
      throw error;
    }
  }

  /**
   * Generate energy report
   */
  async generateEnergyReport(request: ReportRequest): Promise<EnergyReport> {
    try {
      const response = await api.get<ApiResponse<EnergyReport>>('/api/v1/analytics/reports/energy', {
        params: request
      });

      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      throw new Error(response.data.message || 'Failed to generate energy report');
    } catch (error) {
      console.error('Error generating energy report:', error);
      throw error;
    }
  }

  /**
   * Compare data between two periods
   */
  async comparePerformance(
    currentStart: string,
    currentEnd: string,
    previousStart: string,
    previousEnd: string,
    deviceIds?: string[]
  ): Promise<ComparisonResult> {
    try {
      // This would typically involve multiple API calls to get data for both periods
      // For now, we'll implement client-side comparison using existing endpoints
      const [currentData, previousData] = await Promise.all([
        this.getConsumptionTrends({
          interval: 'daily',
          timeRange: '30d', // Adjust based on period
          deviceId: deviceIds?.[0]
        }),
        this.getConsumptionTrends({
          interval: 'daily',
          timeRange: '30d', // Previous period
          deviceId: deviceIds?.[0]
        })
      ]);

      // Calculate comparison metrics (simplified)
      const currentTotal = currentData.reduce((sum, point) => sum + point.value, 0);
      const previousTotal = previousData.reduce((sum, point) => sum + point.value, 0);
      const energyChange = ((currentTotal - previousTotal) / previousTotal) * 100;

      const result: ComparisonResult = {
        current_period: {
          label: `${currentStart} to ${currentEnd}`,
          start_date: currentStart,
          end_date: currentEnd
        },
        previous_period: {
          label: `${previousStart} to ${previousEnd}`,
          start_date: previousStart,
          end_date: previousEnd
        },
        metrics: {
          energy_consumption: {
            current: currentTotal,
            previous: previousTotal,
            change_percentage: energyChange,
            change_absolute: currentTotal - previousTotal
          },
          average_power: {
            current: currentTotal / currentData.length,
            previous: previousTotal / previousData.length,
            change_percentage: 0, // Would calculate based on power data
            change_absolute: 0
          },
          efficiency: {
            current: 0, // Would fetch from efficiency endpoint
            previous: 0,
            change_percentage: 0,
            change_absolute: 0
          },
          cost: {
            current: 0, // Would calculate based on rate
            previous: 0,
            change_percentage: 0,
            change_absolute: 0
          }
        }
      };

      return result;
    } catch (error) {
      console.error('Error comparing performance:', error);
      throw error;
    }
  }

  /**
   * Get analytics summary for dashboard
   */
  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const cacheKey = 'analytics_summary';
    const cached = this.getFromCache<AnalyticsSummary>(cacheKey);
    if (cached) return cached;

    try {
      // Get data with individual error handling to prevent Promise.all from failing
      const [efficiency, alerts] = await Promise.allSettled([
        this.getEfficiencyAnalysis(),
        this.getAlerts(5)
      ]);

      // Extract data with fallbacks
      const efficiencyData = efficiency.status === 'fulfilled' ? efficiency.value : null;
      const alertsData = alerts.status === 'fulfilled' ? alerts.value : null;

      const summary: AnalyticsSummary = {
        total_energy_consumption: 0, // Would calculate from consumption trends
        average_power: 0, // Would calculate from power trends
        system_efficiency: efficiencyData?.overall_efficiency || 75.0, // Fallback value
        total_cost: 0, // Would calculate based on consumption and rates
        active_devices: 0, // Would get from device service
        anomalies_detected: alertsData?.summary.total_alerts || 0, // Fallback value
        peak_demand: 0, // Would calculate from power data
        energy_savings: 0, // Would calculate based on efficiency improvements
        trend_indicators: {
          energy_trend: 'stable',
          efficiency_trend: 'up',
          cost_trend: 'stable'
        }
      };

      this.setCache(cacheKey, summary, 5 * 60 * 1000); // 5 minutes cache
      return summary;
    } catch (error) {
      console.error('Error fetching analytics summary:', error);
      
      // Return empty summary structure instead of mock data
      const emptySummary: AnalyticsSummary = {
        total_energy_consumption: 0,
        average_power: 0,
        system_efficiency: 0,
        total_cost: 0,
        active_devices: 0,
        anomalies_detected: 0,
        peak_demand: 0,
        energy_savings: 0,
        trend_indicators: {
          energy_trend: 'stable',
          efficiency_trend: 'stable',
          cost_trend: 'stable'
        }
      };

      return emptySummary;
    }
  }

  /**
   * Get real-time analytics data with WebSocket support (future enhancement)
   */
  async subscribeToRealTimeData(_callback: (data: any) => void): Promise<() => void> {
    // This would set up WebSocket connection for real-time updates
    // For now, return a no-op unsubscribe function
    console.log('Real-time data subscription would be set up here');
    return () => {
      console.log('Unsubscribing from real-time data');
    };
  }
}

export default new AnalyticsService();
