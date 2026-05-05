import React, { useState } from "react";

interface InteractiveButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  tooltip?: string;
  icon?: React.ReactNode;
  className?: string;
}

export const InteractiveButton: React.FC<InteractiveButtonProps> = ({
  children,
  onClick,
  disabled = false,
  variant = "primary",
  size = "md",
  loading = false,
  tooltip,
  icon,
  className = "",
}) => {
  const [ripples, setRipples] = useState<Array<{ x: number; y: number; id: number }>>([]);
  const [showTooltip, setShowTooltip] = useState(false);

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!disabled && !loading) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const newRipple = { x, y, id: Date.now() };

      setRipples((prev) => [...prev, newRipple]);
      setTimeout(() => {
        setRipples((prev) => prev.filter((r) => r.id !== newRipple.id));
      }, 600);

      onClick?.();
    }
  };

  const btnVariant = variant === "primary" ? "btn-gradient" : "btn-secondary";
  const btnSize =
    size === "sm" ? "ibtn-size-sm" : size === "lg" ? "ibtn-size-lg" : "ibtn-size-md";

  return (
    <div className="ibtn-wrap">
      <button
        type="button"
        className={`btn ibtn ${btnVariant} ${btnSize} ${loading ? "ibtn--loading" : ""} ${className}`}
        onClick={handleClick}
        disabled={disabled || loading}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {ripples.map((ripple) => (
          <span
            key={ripple.id}
            className="ibtn-ripple-host"
            style={{
              left: ripple.x,
              top: ripple.y,
              transform: "translate(-50%, -50%)",
            }}
          >
            <span className="ibtn-ripple" />
          </span>
        ))}

        {loading && <span className="spinner spinner-sm ibtn-spinner" aria-hidden />}

        {icon && !loading && <span className="ibtn-icon">{icon}</span>}

        <span className={loading ? "ibtn-label ibtn-label--muted" : "ibtn-label"}>{children}</span>
      </button>

      {tooltip && showTooltip && !disabled && (
        <div className="ibtn-tooltip" role="tooltip">
          {tooltip}
        </div>
      )}
    </div>
  );
};
