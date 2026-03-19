import React, { useMemo, useState, useCallback, useEffect } from "react";
import type { AnalysisResponse, AnalysisResult } from "./types";
import { GuideModal } from "./components/GuideModal";
import { Tooltip } from "./components/Tooltip";
import { ProgressBar } from "./components/ProgressBar";
import { InteractiveButton } from "./components/InteractiveButton";
import { AnimatedProgress } from "./components/AnimatedProgress";

type Tab = "text" | "file";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

const EXAMPLE_TEXT = `We propose a novel transformer architecture that improves attention efficiency using sparse routing. Our model reduces FLOPs by 40% while maintaining accuracy on GLUE benchmarks. We evaluate on SQuAD and achieve state-of-the-art results with fewer parameters.`;

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("text");
  const [textContent, setTextContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [copiedSection, setCopiedSection] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["clarity", "structure", "technical", "visuals", "summary", "tags"]));
  const [showGuide, setShowGuide] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<Record<string, number>>({});

  const guardrailStatus = result?.guardrails.status;

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setActiveTab("file");
    }
  }, []);

  const copyToClipboard = useCallback((text: string, section: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(section);
    setTimeout(() => setCopiedSection(null), 2000);
  }, []);

  const toggleSection = useCallback((section: string) => {
    const next = new Set(expandedSections);
    if (next.has(section)) {
      next.delete(section);
    } else {
      next.add(section);
    }
    setExpandedSections(next);
  }, [expandedSections]);

  // Keyboard shortcuts
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        if (activeTab === "text" && textContent.trim()) handleAnalyzeText();
        if (activeTab === "file" && file) handleAnalyzeFile();
      }
      if (e.key === "Escape") {
        setShowGuide(false);
        setError(null);
      }
      if (e.key === "?" && !e.shiftKey) {
        e.preventDefault();
        setShowGuide(true);
      }
    };
    window.addEventListener("keydown", down);
    return () => window.removeEventListener("keydown", down);
  }, [activeTab, textContent, file]);

  // Mock progress during analysis
  useEffect(() => {
    if (!isLoading) {
      setAnalysisProgress({});
      return;
    }
    const agents = ["clarity", "structure", "technical", "visuals", "summary", "tags"];
    const interval = setInterval(() => {
      setAnalysisProgress((prev) => {
        const next = { ...prev };
        agents.forEach((agent) => {
          next[agent] = Math.min(100, (next[agent] ?? 0) + Math.random() * 30);
        });
        return next;
      });
    }, 400);
    return () => clearInterval(interval);
  }, [isLoading]);

  const handleAnalyzeText = async () => {
    setError(null);
    setResult(null);
    setCopiedSection(null);
    const trimmed = textContent.trim();
    if (!trimmed) {
      setError("Please paste some text to analyze.");
      return;
    }
    setIsLoading(true);
    try {
      const payload = {
        document: {
          content: trimmed,
          content_type: "markdown",
          source: "text",
        },
      };
      const resp = await fetch(`${API_BASE_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`Backend error ${resp.status}: ${text}`);
      }
      const data: AnalysisResponse = await resp.json();
      setResult(data.result);
    } catch (e: any) {
      setError(e?.message ?? "Failed to analyze text.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeFile = async () => {
    setError(null);
    setResult(null);
    setCopiedSection(null);
    if (!file) {
      setError("Please choose a file to upload.");
      return;
    }
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("content_type", "markdown");

      const resp = await fetch(`${API_BASE_URL}/analyze/file`, {
        method: "POST",
        body: formData,
      });
      if (!resp.ok) {
        const text = await resp.text();
        throw new Error(`Backend error ${resp.status}: ${text}`);
      }
      const data: AnalysisResponse = await resp.json();
      setResult(data.result);
    } catch (e: any) {
      setError(e?.message ?? "Failed to analyze file.");
    } finally {
      setIsLoading(false);
    }
  };

  const guardrailBadge = useMemo(() => {
    if (!result) return null;
    if (guardrailStatus === "ok") {
      return (
        <span className="badge badge-ok">
          Guardrails: OK
        </span>
      );
    }
    return (
      <span className="badge badge-rejected">
        Guardrails: Rejected {result.guardrails.reason && `– ${result.guardrails.reason}`}
      </span>
    );
  }, [result, guardrailStatus]);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Publication Assistant for AI Projects</h1>
          <p className="subtitle">
            Analyze clarity, structure, technical soundness, visuals, summary, and tags
            for your AI/ML paper drafts.
          </p>
        </div>
        <div className="header-actions">
          <Tooltip text="Press '?' for help">
            <button className="btn btn-secondary btn-xs" onClick={() => setShowGuide(true)}>
              ? Help
            </button>
          </Tooltip>
          {guardrailBadge && <div className="guardrail-indicator">{guardrailBadge}</div>}
        </div>
      </header>

      <main className="page-main">
        <section className="card input-card">
          <div className="tabs">
            <button
              className={`tab ${activeTab === "text" ? "tab-active" : ""}`}
              onClick={() => setActiveTab("text")}
              type="button"
            >
              Paste text
            </button>
            <button
              className={`tab ${activeTab === "file" ? "tab-active" : ""}`}
              onClick={() => setActiveTab("file")}
              type="button"
            >
              Upload file
            </button>
          </div>

          {activeTab === "text" && (
            <div className="tab-panel">
              <label className="field-label" htmlFor="document-text">
                Document content
              </label>
              <div className="textarea-wrapper">
                <textarea
                  id="document-text"
                  className="textarea"
                  rows={14}
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  placeholder="Paste your draft here (markdown, LaTeX, or plain text)..."
                />
                <button className="btn btn-xs btn-secondary animate-fade-in" onClick={() => setTextContent(EXAMPLE_TEXT)}>
                  ✨ Load example
                </button>
              </div>
              <div className="actions">
                <InteractiveButton
                  onClick={handleAnalyzeText}
                  disabled={isLoading || !textContent.trim()}
                  loading={isLoading}
                  tooltip={textContent.trim() ? "Analyze your document (Ctrl+Enter)" : "Please enter some text first"}
                  icon="🔍"
                  variant="primary"
                >
                  {isLoading ? "Analyzing..." : "Analyze text"}
                </InteractiveButton>
              </div>
            </div>
          )}

          {activeTab === "file" && (
            <div
              className={`tab-panel file-drop-zone ${dragActive ? "drag-active" : ""}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <label className="field-label" htmlFor="document-file">
                Upload a markdown / text file
              </label>
              <input
                id="document-file"
                type="file"
                accept=".md,.txt"
                onChange={(e) => {
                  const f = e.target.files?.[0] ?? null;
                  setFile(f);
                }}
              />
              <p className="field-help">
                Supported: `.md` and `.txt`. Content is treated as markdown for formatting hints.
              </p>
              {file && (
                <p className="file-selected">
                  Selected: {file.name} ({(file.size / 1024).toFixed(1)} kB)
                </p>
              )}
              <div className="actions">
                <InteractiveButton
                  onClick={handleAnalyzeFile}
                  disabled={isLoading || !file}
                  loading={isLoading}
                  tooltip={file ? "Analyze uploaded file" : "Please select a file first"}
                  icon="📁"
                  variant="primary"
                >
                  {isLoading ? "Analyzing..." : "Analyze file"}
                </InteractiveButton>
              </div>
            </div>
          )}

          {error && (
            <div className="alert alert-error">
              <strong>Error:</strong> {error}
              <button className="btn btn-xs btn-secondary" onClick={() => setError(null)}>
                Dismiss
              </button>
            </div>
          )}

          {isLoading && (
            <div className="progress-sections">
              <h4>Analysis progress</h4>
              {(["clarity", "structure", "technical", "visuals", "summary", "tags"] as const).map((key, index) => (
                <div key={key} className="progress-item" style={{ animationDelay: `${index * 100}ms` }}>
                  <AnimatedProgress
                    value={analysisProgress[key] ?? 0}
                    label={key.charAt(0).toUpperCase() + key.slice(1)}
                    color="blue"
                    size="sm"
                    showPercentage
                    animated
                  />
                </div>
              ))}
            </div>
          )}
        </section>

        {result && (
          <section className="results-grid">
            {[
              { key: "clarity", title: "Clarity", icon: "✨" },
              { key: "structure", title: "Structure", icon: "📋" },
              { key: "technical", title: "Technical review", icon: "🔬" },
              { key: "visuals", title: "Visual suggestions", icon: "📊" },
              { key: "summary", title: "Summary", icon: "📝" },
              { key: "tags", title: "Titles & tags", icon: "🏷️" },
            ].map(({ key, title, icon }) => (
              <div key={key} className="card result-card">
                <h2>
                  <button
                    className="collapser"
                    onClick={() => toggleSection(key)}
                    aria-expanded={expandedSections.has(key)}
                  >
                    {expandedSections.has(key) ? "▼" : "▶"} {icon} {title}
                  </button>
                </h2>
                {expandedSections.has(key) && (
                  <>
                    {key === "clarity" && result.clarity ? (
                      <>
                        <h3>Improved text</h3>
                        <div className="monospace-block with-actions">
                          <pre>{result.clarity.improved_text}</pre>
                          <button
                            className="btn btn-xs"
                            onClick={() => copyToClipboard(result.clarity?.improved_text ?? "", "clarity-improved")}
                          >
                            {copiedSection === "clarity-improved" ? "Copied!" : "Copy"}
                          </button>
                        </div>
                        {result.clarity.comments.length > 0 && (
                          <>
                            <h3>Comments</h3>
                            <ul>
                              {result.clarity.comments.map((c, idx) => (
                                <li key={idx}>{c}</li>
                              ))}
                            </ul>
                          </>
                        )}
                      </>
                    ) : key === "structure" && result.structure ? (
                      <>
                        <h3>Suggested outline</h3>
                        <ul>
                          {result.structure.suggested_outline.map((s, idx) => (
                            <li key={idx}>{s}</li>
                          ))}
                        </ul>
                        {result.structure.section_suggestions.length > 0 && (
                          <>
                            <h3>Section suggestions</h3>
                            <ul>
                              {result.structure.section_suggestions.map((s, idx) => (
                                <li key={idx}>{s}</li>
                              ))}
                            </ul>
                          </>
                        )}
                      </>
                    ) : key === "technical" && result.technical ? (
                      <>
                        {result.technical.issues_found.length > 0 && (
                          <>
                            <h3>Issues found</h3>
                            <ul>
                              {result.technical.issues_found.map((i, idx) => (
                                <li key={idx}>{i}</li>
                              ))}
                            </ul>
                          </>
                        )}
                        {result.technical.suggestions.length > 0 && (
                          <>
                            <h3>Suggestions</h3>
                            <ul>
                              {result.technical.suggestions.map((s, idx) => (
                                <li key={idx}>{s}</li>
                              ))}
                            </ul>
                          </>
                        )}
                      </>
                    ) : key === "visuals" && result.visuals ? (
                      <>
                        {result.visuals.suggestions.length > 0 && (
                          <div className="visual-grid">
                            {result.visuals.suggestions.map((v, idx) => (
                              <article key={idx} className="visual-card">
                                <header className="visual-card-header">
                                  <div className="visual-icon">📊</div>
                                  <div className="visual-title-block">
                                    <h3 className="visual-title">{v.title}</h3>
                                    <span className="visual-type-pill">{v.type}</span>
                                  </div>
                                </header>
                                <p className="visual-description">{v.description}</p>
                              </article>
                            ))}
                          </div>
                        )}
                        {result.visuals.formatting_tips.length > 0 && (
                          <div className="visual-formatting">
                            <h3>Formatting tips</h3>
                            <ul>
                              {result.visuals.formatting_tips.map((t, idx) => (
                                <li key={idx}>{t}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </>
                    ) : key === "summary" && result.summary ? (
                      <>
                        <h3>Abstract</h3>
                        <div className="monospace-block with-actions">
                          <pre>{result.summary.summary}</pre>
                          <button
                            className="btn btn-xs"
                            onClick={() => copyToClipboard(result.summary?.summary ?? "", "summary-abstract")}
                          >
                            {copiedSection === "summary-abstract" ? "Copied!" : "Copy"}
                          </button>
                        </div>
                        {result.summary.key_contributions.length > 0 && (
                          <>
                            <h3>Key contributions</h3>
                            <ul>
                              {result.summary.key_contributions.map((c, idx) => (
                                <li key={idx}>{c}</li>
                              ))}
                            </ul>
                          </>
                        )}
                      </>
                    ) : key === "tags" && result.tags ? (
                      <>
                        {result.tags.title_suggestions.length > 0 && (
                          <div className="titles-section">
                            <h3>Title suggestions</h3>
                            <ol className="title-list">
                              {result.tags.title_suggestions.map((t, idx) => (
                                <li key={idx} className="title-item">
                                  <span className="title-rank">{idx + 1}</span>
                                  <span className="title-text">{t}</span>
                                </li>
                              ))}
                            </ol>
                          </div>
                        )}
                        {result.tags.tags.length > 0 && (
                          <div className="tags-section">
                            <h3>Tags</h3>
                            <div className="tag-chip-row">
                              {result.tags.tags.map((tag, idx) => (
                                <a
                                  key={idx}
                                  className="tag-chip"
                                  href={`https://scholar.google.com/scholar?q=${encodeURIComponent(tag)}`}
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  {tag}
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="placeholder">
                        {key === "clarity" && "Run an analysis to see clarity suggestions."}
                        {key === "structure" && "Outline and structure feedback will appear here."}
                        {key === "technical" && "Technical issues, risks, and suggestions will show up here."}
                        {key === "visuals" && "Diagram, figure, and table suggestions will appear here."}
                        {key === "summary" && "When you run an analysis, a draft abstract and contributions will appear here."}
                        {key === "tags" && "Title candidates and keyword tags will be shown here after analysis."}
                      </p>
                    )}
                  </>
                )}
              </div>
            ))}
          </section>
        )}
      </main>

      <footer className="page-footer">
        <span>Backend: FastAPI · Orchestration: LangGraph · LLM: Groq</span>
      </footer>

      <GuideModal isOpen={showGuide} onClose={() => setShowGuide(false)} />
    </div>
  );
};

export default App;

