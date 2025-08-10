import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface TrendIndicatorProps {
  value: number;
  isIncrease: boolean;
  isDecrease: boolean;
  showIcon?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const TrendIndicator: React.FC<TrendIndicatorProps> = ({
  value,
  isIncrease,
  isDecrease,
  showIcon = true,
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const iconSizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  const getColorClass = () => {
    if (isIncrease) return 'text-green-600';
    if (isDecrease) return 'text-red-600';
    return 'text-gray-600';
  };

  const getTrendIcon = () => {
    if (isIncrease) return TrendingUp;
    if (isDecrease) return TrendingDown;
    return Minus;
  };

  const Icon = getTrendIcon();

  return (
    <div className={`flex items-center ${sizeClasses[size]} ${getColorClass()} ${className}`}>
      {showIcon && (
        <Icon className={`${iconSizeClasses[size]} mr-1`} />
      )}
      <span className="font-medium">
        {isIncrease && '+'}
        {value.toFixed(1)}%
      </span>
    </div>
  );
};

export default TrendIndicator;
