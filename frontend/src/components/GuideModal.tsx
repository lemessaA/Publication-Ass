import React from "react";

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
      title: "2. Optional: limit to a section",
      description:
        "Expand “Section scope” and enter start/end line numbers (1-based, matching your pasted or uploaded file). Only that slice is sent to reviewers. Add a short hint so agents know which part of the paper this is.",
    },
    {
      title: "3. Click Analyze",
      description: "The app will run six agents in parallel to improve clarity, structure, technical soundness, visuals, summary, and tags.",
    },
    {
      title: "4. Review suggestions",
      description:
        "Each section is collapsible. Use the copy button to grab improved text or abstracts. When results are shown, use Export Markdown in the header to download the full report as a .md file.",
    },
    {
      title: "5. Guardrails",
      description: "If content is rejected, you’ll see a badge and reason at the top.",
    },
    {
      title: "6. Keyboard shortcuts",
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
          <button type="button" className="btn btn-gradient btn-sm" onClick={onClose}>
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
