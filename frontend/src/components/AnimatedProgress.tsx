import React from 'react';

interface AnimatedProgressProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  color?: 'blue' | 'green' | 'yellow' | 'red';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
}

export const AnimatedProgress: React.FC<AnimatedProgressProps> = ({
  value,
  max = 100,
  label,
  showPercentage = true,
  color = 'blue',
  size = 'md',
  animated = true,
}) => {
  const percentage = Math.round((value / max) * 100);

  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-emerald-500',
    yellow: 'bg-amber-500',
    red: 'bg-red-500',
  };

  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  };

  const bgColorClasses = {
    blue: 'bg-blue-950/30',
    green: 'bg-emerald-950/30',
    yellow: 'bg-amber-950/30',
    red: 'bg-red-950/30',
  };

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-slate-300">{label}</span>
          {showPercentage && (
            <span className="text-sm text-slate-500">{percentage}%</span>
          )}
        </div>
      )}
      <div className={`relative ${sizeClasses[size]} ${bgColorClasses[color]} rounded-full overflow-hidden`}>
        <div
          className={`absolute top-0 left-0 h-full ${colorClasses[color]} rounded-full transition-all duration-500 ease-out ${
            animated ? 'animate-pulse' : ''
          }`}
          style={{ width: `${percentage}%` }}
        >
          {animated && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer" />
          )}
        </div>
      </div>
    </div>
  );
};
