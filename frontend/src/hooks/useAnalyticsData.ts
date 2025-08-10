import { useQuery, UseQueryResult } from 'react-query';
import analyticsService from '../services/analyticsService';
import {
  ChartParams,
  EfficiencyAnalysis,
  AlertsResponse,
  ForecastData,
  EnergyReport,
  AnalyticsSummary
} from '../types/analytics';
import { ChartDataPoint } from '../types';

/**
 * Hook for fetching analytics summary data
 */
export const useAnalyticsSummary = (
  refetchInterval: number = 5 * 60 * 1000 // 5 minutes
): UseQueryResult<AnalyticsSummary, Error> => {
  return useQuery(
    'analytics-summary',
    () => analyticsService.getAnalyticsSummary(),
    {
      refetchInterval,
      staleTime: 2 * 60 * 1000, // 2 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    }
  );
};

/**
 * Hook for fetching consumption trends data
 */
export const useConsumptionTrends = (
  params: ChartParams,
  enabled: boolean = true,
  refetchInterval: number = 30000 // 30 seconds
): UseQueryResult<ChartDataPoint[], Error> => {
  return useQuery(
    ['consumption-trends', params],
    () => analyticsService.getConsumptionTrends(params),
    {
      enabled,
      refetchInterval,
      staleTime: 1 * 60 * 1000, // 1 minute
      cacheTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch consumption trends:', error);
      },
    }
  );
};

/**
 * Hook for fetching power trends data
 */
export const usePowerTrends = (
  params: ChartParams,
  enabled: boolean = true,
  refetchInterval: number = 30000 // 30 seconds
): UseQueryResult<ChartDataPoint[], Error> => {
  return useQuery(
    ['power-trends', params],
    () => analyticsService.getPowerTrends(params),
    {
      enabled,
      refetchInterval,
      staleTime: 1 * 60 * 1000, // 1 minute
      cacheTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch power trends:', error);
      },
    }
  );
};

/**
 * Hook for fetching efficiency analysis
 */
export const useEfficiencyAnalysis = (
  refetchInterval: number = 10 * 60 * 1000 // 10 minutes
): UseQueryResult<EfficiencyAnalysis, Error> => {
  return useQuery(
    'efficiency-analysis',
    () => analyticsService.getEfficiencyAnalysis(),
    {
      refetchInterval,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 15 * 60 * 1000, // 15 minutes
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch efficiency analysis:', error);
      },
    }
  );
};

/**
 * Hook for fetching alerts data
 */
export const useAlerts = (
  limit: number = 20,
  refetchInterval: number = 60000 // 1 minute
): UseQueryResult<AlertsResponse, Error> => {
  return useQuery(
    ['alerts', limit],
    () => analyticsService.getAlerts(limit),
    {
      refetchInterval,
      staleTime: 30 * 1000, // 30 seconds
      cacheTime: 2 * 60 * 1000, // 2 minutes
      retry: 3,
      onError: (error) => {
        console.error('Failed to fetch alerts:', error);
      },
    }
  );
};

/**
 * Hook for fetching forecast data
 */
export const useForecast = (
  daysAhead: number = 30,
  enabled: boolean = true,
  refetchInterval: number = 30 * 60 * 1000 // 30 minutes
): UseQueryResult<ForecastData, Error> => {
  return useQuery(
    ['forecast', daysAhead],
    () => analyticsService.getForecast(daysAhead),
    {
      enabled,
      refetchInterval,
      staleTime: 15 * 60 * 1000, // 15 minutes
      cacheTime: 60 * 60 * 1000, // 1 hour
      retry: 2,
      onError: (error) => {
        console.error('Failed to fetch forecast:', error);
      },
    }
  );
};

/**
 * Hook for generating energy reports
 */
export const useEnergyReport = (
  request: {
    start_date: string;
    end_date: string;
    device_ids?: string[];
  },
  enabled: boolean = false // Manual trigger
): UseQueryResult<EnergyReport, Error> => {
  return useQuery(
    ['energy-report', request],
    () => analyticsService.generateEnergyReport(request),
    {
      enabled,
      retry: 1,
      cacheTime: 0, // Don't cache reports
      onError: (error) => {
        console.error('Failed to generate energy report:', error);
      },
    }
  );
};

/**
 * Combined hook for fetching all analytics data needed for the main analytics page
 */
export const useAnalyticsData = (params: ChartParams) => {
  const summary = useAnalyticsSummary();
  const consumptionTrends = useConsumptionTrends(params);
  const powerTrends = usePowerTrends(params);
  const efficiency = useEfficiencyAnalysis();
  const alerts = useAlerts(5); // Only recent alerts for summary
  const forecast = useForecast(30);

  return {
    summary,
    consumptionTrends,
    powerTrends,
    efficiency,
    alerts,
    forecast,
    isLoading: summary.isLoading || consumptionTrends.isLoading || powerTrends.isLoading,
    hasError: summary.error || consumptionTrends.error || powerTrends.error || efficiency.error,
    refetchAll: () => {
      summary.refetch();
      consumptionTrends.refetch();
      powerTrends.refetch();
      efficiency.refetch();
      alerts.refetch();
      forecast.refetch();
    },
  };
};

/**
 * Hook for real-time data subscription (future enhancement)
 */
export const useRealTimeAnalytics = (_enabled: boolean = false) => {
  // This would set up WebSocket connection for real-time updates
  // For now, just return placeholder
  return {
    isConnected: false,
    lastUpdate: null,
    subscribe: () => console.log('Real-time subscription would start here'),
    unsubscribe: () => console.log('Real-time subscription would stop here'),
  };
};
