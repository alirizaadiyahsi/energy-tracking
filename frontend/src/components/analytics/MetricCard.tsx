import React from 'react';
import { LucideIcon } from 'lucide-react';
import TrendIndicator from './TrendIndicator';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: {
    value: number;
    isIncrease: boolean;
    isDecrease: boolean;
  };
  icon: LucideIcon;
  color: string;
  bgColor: string;
  onClick?: () => void;
  isLoading?: boolean;
  showTrend?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  color,
  bgColor,
  onClick,
  isLoading = false,
  showTrend = true,
  size = 'md',
}) => {
  const sizeClasses = {
    sm: {
      card: 'p-4',
      icon: 'h-5 w-5',
      iconContainer: 'p-2',
      title: 'text-xs',
      value: 'text-lg',
    },
    md: {
      card: 'p-5',
      icon: 'h-6 w-6',
      iconContainer: 'p-3',
      title: 'text-sm',
      value: 'text-2xl',
    },
    lg: {
      card: 'p-6',
      icon: 'h-7 w-7',
      iconContainer: 'p-4',
      title: 'text-base',
      value: 'text-3xl',
    },
  };

  if (isLoading) {
    return (
      <div className={`card ${sizeClasses[size].card} ${onClick ? 'cursor-pointer' : ''}`}>
        <div className="flex items-center">
          <div className={`flex-shrink-0 ${sizeClasses[size].iconContainer} rounded-lg ${bgColor} animate-pulse`}>
            <div className={`${sizeClasses[size].icon} bg-gray-400 rounded`}></div>
          </div>
          <div className="ml-4 flex-1">
            <div className="h-4 bg-gray-200 rounded animate-pulse mb-2"></div>
            <div className="h-6 bg-gray-300 rounded animate-pulse mb-1"></div>
            {subtitle && <div className="h-3 bg-gray-200 rounded animate-pulse"></div>}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`card ${sizeClasses[size].card} ${
        onClick ? 'cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-105' : ''
      }`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      <div className="flex items-center">
        <div className={`flex-shrink-0 ${sizeClasses[size].iconContainer} rounded-lg ${bgColor}`}>
          <Icon className={`${sizeClasses[size].icon} ${color}`} />
        </div>
        <div className="ml-4 flex-1">
          <div className="flex items-center justify-between mb-1">
            <p className={`${sizeClasses[size].title} font-medium text-secondary-600`}>
              {title}
            </p>
            {trend && showTrend && (
              <TrendIndicator
                value={trend.value}
                isIncrease={trend.isIncrease}
                isDecrease={trend.isDecrease}
                size="sm"
              />
            )}
          </div>
          <p className={`${sizeClasses[size].value} font-semibold text-secondary-900`}>
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-secondary-500 mt-1">{subtitle}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default MetricCard;
