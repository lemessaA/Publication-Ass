import React, { useState } from 'react';

interface InteractiveButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  tooltip?: string;
  icon?: React.ReactNode;
  className?: string;
}

export const InteractiveButton: React.FC<InteractiveButtonProps> = ({
  children,
  onClick,
  disabled = false,
  variant = 'primary',
  size = 'md',
  loading = false,
  tooltip,
  icon,
  className = '',
}) => {
  const [ripples, setRipples] = useState<Array<{ x: number; y: number; id: number }>>([]);
  const [showTooltip, setShowTooltip] = useState(false);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!disabled && !loading) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const newRipple = { x, y, id: Date.now() };
      
      setRipples(prev => [...prev, newRipple]);
      setTimeout(() => {
        setRipples(prev => prev.filter(r => r.id !== newRipple.id));
      }, 600);

      onClick?.();
    }
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-800',
    secondary: 'bg-slate-700 text-slate-200 hover:bg-slate-600 focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 focus:ring-offset-slate-800'
  };

  return (
    <div className="relative inline-block">
      <button
        className={`
          relative overflow-hidden inline-flex items-center justify-center
          rounded-lg font-medium transition-all duration-200
          transform hover:scale-105 active:scale-95
          disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
          ${sizeClasses[size]}
          ${variantClasses[variant]}
          ${className}
        `}
        onClick={handleClick}
        disabled={disabled || loading}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {/* Ripple effects */}
        {ripples.map(ripple => (
          <span
            key={ripple.id}
            className="absolute pointer-events-none"
            style={{
              left: ripple.x,
              top: ripple.y,
              transform: 'translate(-50%, -50%)',
            }}
          >
            <span className="inline-block w-8 h-8 bg-white opacity-30 rounded-full animate-ping" />
          </span>
        ))}

        {/* Loading spinner */}
        {loading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}

        {/* Icon */}
        {icon && !loading && <span className="mr-2">{icon}</span>}

        {/* Content */}
        <span className={loading ? 'opacity-70' : ''}>{children}</span>
      </button>

      {/* Tooltip */}
      {tooltip && showTooltip && !disabled && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 text-white text-sm rounded whitespace-nowrap z-50 animate-fade-in border border-slate-700">
          {tooltip}
          <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
            <div className="border-4 border-transparent border-t-slate-900"></div>
          </div>
        </div>
      )}
    </div>
  );
};
