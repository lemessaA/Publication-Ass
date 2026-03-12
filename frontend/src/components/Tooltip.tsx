import React, { useState } from "react";

interface TooltipProps {
  text: string;
  children: React.ReactNode;
  placement?: "top" | "bottom" | "left" | "right";
}

export const Tooltip: React.FC<TooltipProps> = ({ text, children, placement = "top" }) => {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className="tooltip-wrapper"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div className={`tooltip tooltip-${placement}`}>
          {text}
          <span className="tooltip-arrow"></span>
        </div>
      )}
    </div>
  );
};
