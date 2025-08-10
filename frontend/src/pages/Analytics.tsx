import React, { useState } from 'react';
import TimeIntervalSelector, { TimeIntervalOption, timeIntervals } from '../components/TimeIntervalSelector';
import AnalyticsSummaryCards from '../components/analytics/AnalyticsSummaryCards';
import ConsumptionTrendsChart from '../components/analytics/ConsumptionTrendsChart';
import PowerUsageChart from '../components/analytics/PowerUsageChart';
import EfficiencyAnalysis from '../components/analytics/EfficiencyAnalysis';
import AnomalyDetectionPanel from '../components/analytics/AnomalyDetectionPanel';
import ConsumptionForecast from '../components/analytics/ConsumptionForecast';
import ComparativeAnalysis from '../components/analytics/ComparativeAnalysis';
import DevicePerformanceTable from '../components/analytics/DevicePerformanceTable';
import EnergyReportsGenerator from '../components/analytics/EnergyReportsGenerator';
import { useAnalyticsSummary } from '../hooks/useAnalyticsData';
import { ChartParams } from '../types/analytics';

const Analytics: React.FC = () => {
  // State for time interval selection
  const [selectedInterval, setSelectedInterval] = useState<TimeIntervalOption>(timeIntervals[1]); // Default to hourly 24h
  
  // State for chart parameters
  const [chartParams, setChartParams] = useState<ChartParams>({
    interval: 'hourly',
    timeRange: '24h',
  });
  
  // Fetch analytics summary data
  const { data: summaryData, isLoading: summaryLoading, error: summaryError } = useAnalyticsSummary();

  if (summaryLoading && !summaryData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const handleCardClick = (metric: string) => {
    console.log(`Clicked on metric: ${metric}`);
    // TODO: Implement filtering or navigation based on clicked metric
  };

  const handleIntervalChange = (interval: TimeIntervalOption) => {
    setSelectedInterval(interval);
    setChartParams(prev => ({
      ...prev,
      interval: interval.interval,
      timeRange: interval.timeRange,
    }));
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Page Header */}
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-secondary-900">Analytics</h1>
          <p className="mt-2 text-sm text-secondary-700">
            Comprehensive analysis of your energy consumption patterns and trends
          </p>
        </div>
      </div>

      {/* Summary Metrics Cards */}
      <div className="mt-8">
        {summaryError ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-600 text-sm">
              Failed to load analytics summary. Please try refreshing the page.
            </p>
          </div>
        ) : (
          <AnalyticsSummaryCards
            data={summaryData}
            isLoading={summaryLoading}
            onCardClick={handleCardClick}
          />
        )}
      </div>

      {/* Time Range Selector */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-secondary-900">Energy Analytics</h2>
          <TimeIntervalSelector
            selectedInterval={selectedInterval}
            onIntervalChange={handleIntervalChange}
          />
        </div>
      </div>

      {/* Main Charts Section */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Energy Consumption Trends Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-secondary-900">Energy Consumption Trends</h3>
            <div className="flex space-x-2">
              <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
              <span className="text-sm text-secondary-600">Real-time data</span>
            </div>
          </div>
          <ConsumptionTrendsChart
            params={chartParams}
            onParamsChange={setChartParams}
            height={320}
            showControls={false}
            showStats={true}
          />
        </div>

        {/* Power Usage Analytics Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-secondary-900">Power Usage Analytics</h3>
            <div className="flex space-x-2">
              <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
              <span className="text-sm text-secondary-600">Live monitoring</span>
            </div>
          </div>
          <PowerUsageChart
            params={chartParams}
            onParamsChange={setChartParams}
            height={320}
            showControls={false}
            showPeakDetection={true}
          />
        </div>
      </div>

      {/* Efficiency Analysis - Full Width */}
      <div className="mt-8">
        <div className="card">
          <h3 className="text-lg font-medium text-secondary-900 mb-4">Efficiency Analysis</h3>
          <EfficiencyAnalysis
            params={chartParams}
            showRecommendations={true}
          />
        </div>
      </div>

      {/* Secondary Analytics Section */}
      <div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Forecasting Component */}
        <div className="card">
          <ConsumptionForecast
            params={chartParams}
            onParamsChange={setChartParams}
            height={320}
            showControls={true}
            forecastDays={30}
            confidenceInterval={true}
          />
        </div>

        {/* Anomaly Detection Panel */}
        <div className="card">
          <AnomalyDetectionPanel
            maxAlerts={10}
            showResolvedAlerts={false}
            autoRefresh={true}
          />
        </div>
      </div>

      {/* Comparative Analysis and Device Performance - Placeholder */}
      <div className="mt-8 grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Comparative Analysis Component */}
        <div className="xl:col-span-2 card">
          <ComparativeAnalysis
            params={chartParams}
            onParamsChange={setChartParams}
            height={360}
            showControls={true}
          />
        </div>

        {/* Device Performance Table */}
        <div className="card">
          <DevicePerformanceTable />
        </div>
      </div>

      {/* Reports Section */}
      <div className="mt-8 mb-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <EnergyReportsGenerator />
        </div>
      </div>
    </div>
  );
};

export default Analytics;
