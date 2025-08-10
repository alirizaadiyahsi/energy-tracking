import React, { useState, useMemo } from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Info, Lightbulb } from 'lucide-react';
import { useEfficiencyAnalysis } from '../../hooks/useAnalyticsData';
import { ChartParams } from '../../types/analytics';
import { formatAnalyticsValue } from '../../utils/analyticsTransformers';

interface EfficiencyAnalysisProps {
  params: ChartParams;
  deviceId?: string;
  showRecommendations?: boolean;
}

interface EfficiencyMetricProps {
  title: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendValue: number;
  target?: number;
  description: string;
}

const EfficiencyMetric: React.FC<EfficiencyMetricProps> = ({
  title,
  value,
  unit,
  trend,
  trendValue,
  target,
  description,
}) => {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      default:
        return <div className="h-4 w-4 bg-gray-400 rounded-full" />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusColor = () => {
    if (!target) return 'bg-blue-50 border-blue-200';
    
    if (value >= target) {
      return 'bg-green-50 border-green-200';
    } else if (value >= target * 0.8) {
      return 'bg-yellow-50 border-yellow-200';
    } else {
      return 'bg-red-50 border-red-200';
    }
  };

  const getStatusIcon = () => {
    if (!target) return <Info className="h-4 w-4 text-blue-500" />;
    
    if (value >= target) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    } else if (value >= target * 0.8) {
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    } else {
      return <AlertTriangle className="h-4 w-4 text-red-500" />;
    }
  };

  return (
    <div className={`p-4 rounded-lg border ${getStatusColor()}`}>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700">{title}</h4>
        {getStatusIcon()}
      </div>
      
      <div className="flex items-center space-x-2 mb-1">
        <span className="text-2xl font-bold text-gray-900">
          {value.toFixed(1)}
        </span>
        <span className="text-sm text-gray-500">{unit}</span>
        <div className="flex items-center space-x-1">
          {getTrendIcon()}
          <span className={`text-xs font-medium ${getTrendColor()}`}>
            {Math.abs(trendValue).toFixed(1)}%
          </span>
        </div>
      </div>
      
      {target && (
        <div className="text-xs text-gray-600 mb-2">
          Target: {target.toFixed(1)} {unit}
        </div>
      )}
      
      <p className="text-xs text-gray-600">{description}</p>
    </div>
  );
};

interface RecommendationCardProps {
  title: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  effort: 'easy' | 'moderate' | 'complex';
  savings: string;
  category: 'immediate' | 'short-term' | 'long-term';
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({
  title,
  description,
  impact,
  effort,
  savings,
  category,
}) => {
  const getImpactColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'bg-green-100 text-green-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'immediate':
        return 'bg-red-100 text-red-800';
      case 'short-term':
        return 'bg-orange-100 text-orange-800';
      case 'long-term':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <Lightbulb className="h-5 w-5 text-yellow-500" />
          <h4 className="font-medium text-gray-900">{title}</h4>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${getCategoryColor(category)}`}>
          {category}
        </span>
      </div>
      
      <p className="text-sm text-gray-600 mb-3">{description}</p>
      
      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${getImpactColor(impact)}`}>
            {impact} impact
          </span>
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${getImpactColor(effort)}`}>
            {effort} effort
          </span>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500">Potential savings</p>
          <p className="text-sm font-semibold text-green-600">{savings}</p>
        </div>
      </div>
    </div>
  );
};

const EfficiencyAnalysis: React.FC<EfficiencyAnalysisProps> = ({
  params: _params,
  deviceId: _deviceId,
  showRecommendations = true,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'immediate' | 'short-term' | 'long-term'>('all');
  
  const { data: efficiencyData, isLoading, error } = useEfficiencyAnalysis();

  const recommendations = useMemo(() => [
    {
      title: 'Optimize Peak Hours Usage',
      description: 'Shift non-essential loads to off-peak hours to reduce demand charges and improve grid efficiency.',
      impact: 'high' as const,
      effort: 'easy' as const,
      savings: '15-25%',
      category: 'immediate' as const,
    },
    {
      title: 'Implement Power Factor Correction',
      description: 'Install capacitor banks to improve power factor and reduce reactive power consumption.',
      impact: 'medium' as const,
      effort: 'moderate' as const,
      savings: '8-12%',
      category: 'short-term' as const,
    },
    {
      title: 'Upgrade to Variable Speed Drives',
      description: 'Replace constant speed motors with variable frequency drives for better energy efficiency.',
      impact: 'high' as const,
      effort: 'complex' as const,
      savings: '20-30%',
      category: 'long-term' as const,
    },
    {
      title: 'Enable Smart Scheduling',
      description: 'Use automated scheduling to run equipment during optimal efficiency windows.',
      impact: 'medium' as const,
      effort: 'easy' as const,
      savings: '10-15%',
      category: 'immediate' as const,
    },
    {
      title: 'Regular Equipment Maintenance',
      description: 'Maintain equipment at peak performance through preventive maintenance programs.',
      impact: 'medium' as const,
      effort: 'moderate' as const,
      savings: '5-10%',
      category: 'short-term' as const,
    },
  ], []);

  const filteredRecommendations = useMemo(() => {
    if (selectedCategory === 'all') return recommendations;
    return recommendations.filter(rec => rec.category === selectedCategory);
  }, [recommendations, selectedCategory]);

  const mockData = useMemo(() => ({
    efficiency: efficiencyData?.overall_efficiency || 78.5,
    powerFactor: 0.92,
    loadFactor: 0.68,
    costPerKwh: 0.14,
    potentialSavings: 5420
  }), [efficiencyData]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <p className="text-red-600 font-medium">Failed to load efficiency analysis</p>
        </div>
        <p className="text-red-500 text-sm mt-1">{error.message}</p>
      </div>
    );
  }

  if (!efficiencyData) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="text-center">
          <Info className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-600">No efficiency data available</p>
          <p className="text-gray-500 text-sm">Try adjusting the time range or parameters</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Efficiency Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <EfficiencyMetric
          title="Energy Efficiency"
          value={mockData.efficiency}
          unit="%"
          trend={mockData.efficiency > 85 ? 'up' : mockData.efficiency > 70 ? 'stable' : 'down'}
          trendValue={5.2}
          target={90}
          description="Overall energy conversion efficiency"
        />
        
        <EfficiencyMetric
          title="Power Factor"
          value={mockData.powerFactor * 100}
          unit="%"
          trend={mockData.powerFactor > 0.95 ? 'up' : mockData.powerFactor > 0.85 ? 'stable' : 'down'}
          trendValue={2.1}
          target={95}
          description="Ratio of real to apparent power"
        />
        
        <EfficiencyMetric
          title="Load Factor"
          value={mockData.loadFactor * 100}
          unit="%"
          trend={mockData.loadFactor > 0.7 ? 'up' : mockData.loadFactor > 0.5 ? 'stable' : 'down'}
          trendValue={-1.5}
          target={75}
          description="Average vs peak demand ratio"
        />
        
        <EfficiencyMetric
          title="Cost per kWh"
          value={mockData.costPerKwh}
          unit="$/kWh"
          trend={mockData.costPerKwh < 0.12 ? 'up' : mockData.costPerKwh < 0.15 ? 'stable' : 'down'}
          trendValue={-3.2}
          target={0.10}
          description="Average energy cost including demand charges"
        />
      </div>

      {/* Recommendations Section */}
      {showRecommendations && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Optimization Recommendations</h3>
            <div className="flex space-x-2">
              {['all', 'immediate', 'short-term', 'long-term'].map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category as any)}
                  className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                    selectedCategory === category
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </button>
              ))}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredRecommendations.map((recommendation, index) => (
              <RecommendationCard
                key={index}
                {...recommendation}
              />
            ))}
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="bg-gradient-to-r from-blue-50 to-green-50 p-4 rounded-lg border border-blue-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-600">Potential Annual Savings</p>
            <p className="text-2xl font-bold text-green-600">
              {formatAnalyticsValue(mockData.potentialSavings, 'currency')}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">CO₂ Reduction Potential</p>
            <p className="text-2xl font-bold text-blue-600">
              {((mockData.efficiency / 100) * 12.5).toFixed(1)} tons/year
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Efficiency Score</p>
            <p className="text-2xl font-bold text-purple-600">
              {Math.round((mockData.efficiency + mockData.powerFactor * 100 + mockData.loadFactor * 100) / 3)}/100
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EfficiencyAnalysis;
