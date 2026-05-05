import React, { useMemo, useState, useCallback, useEffect } from "react";
import type { AnalysisResponse, AnalysisResult, HistoryItem } from "./types";
import type { Theme } from "./theme";
import { applyTheme, resolveTheme, toggleTheme as themeFlip } from "./theme";
import { GuideModal } from "./components/GuideModal";
import { Tooltip } from "./components/Tooltip";
import { InteractiveButton } from "./components/InteractiveButton";
import { ThemeToggle } from "./components/ThemeToggle";

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
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [loadingHistoryId, setLoadingHistoryId] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>(() => resolveTheme());

  const guardrailStatus = result?.guardrails.status;

  const handleThemeToggle = useCallback(() => {
    setTheme((prev) => themeFlip(prev));
  }, []);

  const refreshHistory = useCallback(async () => {
    setHistoryError(null);
    try {
      const resp = await fetch(`${API_BASE_URL}/history`);
      if (!resp.ok) {
        setHistoryItems([]);
        return;
      }
      const data: HistoryItem[] = await resp.json();
      setHistoryItems(data);
    } catch {
      setHistoryError("Could not load history (is the API running and CORS configured?)");
      setHistoryItems([]);
    }
  }, []);

  const openHistoryItem = useCallback(
    async (id: string) => {
      setError(null);
      setLoadingHistoryId(id);
      try {
        const resp = await fetch(`${API_BASE_URL}/history/${id}`);
        if (!resp.ok) {
          const text = await resp.text();
          throw new Error(`Could not open saved analysis: ${resp.status} ${text}`);
        }
        const item: HistoryItem = await resp.json();
        setResult(item.result);
        setCopiedSection(null);
        requestAnimationFrame(() => {
          document.getElementById("analysis-results")?.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Failed to load history item.");
      } finally {
        setLoadingHistoryId(null);
      }
    },
    []
  );

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

  useEffect(() => {
    void refreshHistory();
  }, [refreshHistory]);

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
      void refreshHistory();
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
      void refreshHistory();
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
          <ThemeToggle theme={theme} onToggle={handleThemeToggle} />
          <Tooltip text="Press '?' for help">
            <button className="btn btn-secondary btn-xs" onClick={() => setShowGuide(true)}>
              ? Help
            </button>
          </Tooltip>
          {guardrailBadge && <div className="guardrail-indicator">{guardrailBadge}</div>}
        </div>
      </header>

      <main className="page-main">
        <section className="page-section">
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
                <button className="btn btn-xs btn-secondary animate-fade-in" type="button" onClick={() => setTextContent(EXAMPLE_TEXT)}>
                  Load example
                </button>
              </div>
              <div className="actions">
                <InteractiveButton
                  onClick={handleAnalyzeText}
                  disabled={isLoading || !textContent.trim()}
                  loading={isLoading}
                  tooltip={textContent.trim() ? "Analyze your document (Ctrl+Enter)" : "Please enter some text first"}
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
            <div className="analysis-loading" role="status" aria-live="polite">
              <div className="spinner spinner-lg" aria-hidden />
              <div className="analysis-loading-text">
                <strong>Running analysis…</strong>
                <p className="analysis-loading-hint">
                  Multiple reviewers run in parallel on the server; this may take up to a minute.
                </p>
              </div>
            </div>
          )}
        </section>

        <section className="page-section page-section--history">
          <div className="history-header">
            <h2 className="history-title">Saved analyses</h2>
            <button type="button" className="btn btn-xs btn-secondary" onClick={() => void refreshHistory()}>
              Refresh
            </button>
          </div>
          <p className="field-help history-help">
            Appears when the server uses <code>HISTORY_BACKEND=file</code>. Otherwise the list stays empty.
          </p>
          {historyError && (
            <div className="alert alert-error history-alert">
              {historyError}
            </div>
          )}
          {historyItems.length === 0 && !historyError ? (
            <p className="history-empty">No saved analyses yet.</p>
          ) : (
            <ul className="history-list">
              {historyItems.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    className="history-row"
                    onClick={() => void openHistoryItem(item.id)}
                    disabled={loadingHistoryId === item.id}
                  >
                    <span className="history-date">
                      {new Date(item.created_at).toLocaleString(undefined, {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </span>
                    <span className="history-id">{item.id.slice(0, 8)}…</span>
                    {loadingHistoryId === item.id ? <span className="history-loading">Loading…</span> : null}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        {result && result.analysis_warnings && result.analysis_warnings.length > 0 && (
          <div className="alert alert-warn" role="status">
            {result.analysis_warnings.map((w, idx) => (
              <p key={idx}>{w}</p>
            ))}
          </div>
        )}

        {result && (
          <section className="results-stack" id="analysis-results">
            {[
              { key: "clarity", title: "Clarity" },
              { key: "structure", title: "Structure" },
              { key: "technical", title: "Technical review" },
              { key: "visuals", title: "Visual suggestions" },
              { key: "summary", title: "Summary" },
              { key: "tags", title: "Titles & tags" },
            ].map(({ key, title }) => (
              <section key={key} className="analysis-block">
                <h2>
                  <button
                    className="collapser"
                    onClick={() => toggleSection(key)}
                    aria-expanded={expandedSections.has(key)}
                  >
                    <span className="collapser-chevron" aria-hidden>
                      {expandedSections.has(key) ? "▼" : "▶"}
                    </span>
                    <span className="collapser-title">{title}</span>
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
                              <article key={idx} className="visual-item">
                                <header className="visual-item-header">
                                  <span className="visual-dot" aria-hidden />
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
              </section>
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

