import React from "react";

interface ProgressBarProps {
  percent: number;
  label?: string;
  color?: "primary" | "success" | "error";
  size?: "sm" | "md";
}

export const ProgressBar: React.FC<ProgressBarProps> = ({ percent, label, color = "primary", size = "md" }) => {
  return (
    <div className={`progress progress-${size}`}>
      {label && <span className="progress-label">{label}</span>}
      <div className="progress-bar-bg">
        <div
          className={`progress-bar-fill progress-bar-${color}`}
          style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
        ></div>
      </div>
    </div>
  );
};
