import React, { useMemo, useState } from "react";
import type { AnalysisResponse, AnalysisResult } from "./types";

type Tab = "text" | "file";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("text");
  const [textContent, setTextContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const guardrailStatus = result?.guardrails.status;

  const handleAnalyzeText = async () => {
    setError(null);
    setResult(null);
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
        {guardrailBadge && <div className="guardrail-indicator">{guardrailBadge}</div>}
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
              <textarea
                id="document-text"
                className="textarea"
                rows={14}
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                placeholder="Paste your draft here (markdown, LaTeX, or plain text)..."
              />
              <div className="actions">
                <button
                  className="btn primary"
                  type="button"
                  onClick={handleAnalyzeText}
                  disabled={isLoading}
                >
                  {isLoading ? "Analyzing..." : "Analyze text"}
                </button>
              </div>
            </div>
          )}

          {activeTab === "file" && (
            <div className="tab-panel">
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
              <div className="actions">
                <button
                  className="btn primary"
                  type="button"
                  onClick={handleAnalyzeFile}
                  disabled={isLoading}
                >
                  {isLoading ? "Analyzing..." : "Analyze file"}
                </button>
              </div>
            </div>
          )}

          {error && <div className="alert alert-error">{error}</div>}
        </section>

        <section className="results-grid">
          <div className="card result-card">
            <h2>Clarity</h2>
            {result?.clarity ? (
              <>
                <h3>Improved text</h3>
                <p className="monospace-block">{result.clarity.improved_text}</p>
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
            ) : (
              <p className="placeholder">Run an analysis to see clarity suggestions.</p>
            )}

            <h2>Structure</h2>
            {result?.structure ? (
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
            ) : (
              <p className="placeholder">Outline and structure feedback will appear here.</p>
            )}
          </div>

          <div className="card result-card">
            <h2>Technical review</h2>
            {result?.technical ? (
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
            ) : (
              <p className="placeholder">
                Technical issues, risks, and suggestions will show up here.
              </p>
            )}

            <h2>Visual suggestions</h2>
            {result?.visuals ? (
              <>
                {result.visuals.suggestions.length > 0 && (
                  <div className="visual-grid">
                    {result.visuals.suggestions.map((v, idx) => (
                      <article key={idx} className="visual-card">
                        <header className="visual-card-header">
                          <div className="visual-icon">
                            <span>📊</span>
                          </div>
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
            ) : (
              <p className="placeholder">
                Diagram, figure, and table suggestions will appear here.
              </p>
            )}
          </div>

          <div className="card result-card">
            <h2>Summary</h2>
            {result?.summary ? (
              <>
                <h3>Abstract</h3>
                <p>{result.summary.summary}</p>
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
            ) : (
              <p className="placeholder">
                When you run an analysis, a draft abstract and contributions will appear here.
              </p>
            )}

            <h2>Titles &amp; tags</h2>
            {result?.tags ? (
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
                Title candidates and keyword tags will be shown here after analysis.
              </p>
            )}
          </div>
        </section>
      </main>

      <footer className="page-footer">
        <span>Backend: FastAPI · Orchestration: LangGraph · LLM: Groq</span>
      </footer>
    </div>
  );
};

export default App;

