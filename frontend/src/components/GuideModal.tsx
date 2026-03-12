import React, { useState } from "react";

interface GuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GuideModal: React.FC<GuideModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const steps = [
    {
      title: "1. Paste or upload your draft",
      description: "Use the text tab to paste markdown/LaTeX/plain text, or drag & drop a .md/.txt file.",
    },
    {
      title: "2. Click Analyze",
      description: "The app will run six agents in parallel to improve clarity, structure, technical soundness, visuals, summary, and tags.",
    },
    {
      title: "3. Review suggestions",
      description: "Each section is collapsible. Use the copy button to grab improved text or abstracts.",
    },
    {
      title: "4. Guardrails",
      description: "If content is rejected, you’ll see a badge and reason at the top.",
    },
    {
      title: "5. Keyboard shortcuts",
      description: "Press Ctrl+Enter (or Cmd+Enter) to analyze, Escape to close modals.",
    },
  ];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>How to use Publication Assistant</h2>
          <button className="btn btn-xs btn-secondary" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="modal-body">
          {steps.map((step, idx) => (
            <div key={idx} className="guide-step">
              <h3>{step.title}</h3>
              <p>{step.description}</p>
            </div>
          ))}
        </div>
        <div className="modal-footer">
          <button className="btn primary" onClick={onClose}>
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
