# Feature roadmap — step by step

Work through phases in order when building out Publication Assistant. Each block lists **steps** (ordered) and **done when** criteria.

---

## Phase 1 — Ship-ready polish ✅ *implemented (see code & `exportReport.ts`)*

### 1A — Export report as Markdown ✅
**Steps**
1. ~~Add `analysisResultToMarkdown()`~~ — `frontend/src/exportReport.ts`.
2. ~~**Export Markdown** button~~ — appears in the header when results exist; downloads `.md` via `Blob`.
3. *(Optional)* Add `GET /api/v1/export/{format}` later for PDFs.

**Done when:** User downloads a `.md` with all sections — **met.**

### 1B — Reviewer persona (environment-driven) ✅
**Steps**
1. ~~`REVIEWER_PERSONA` in config~~ — `app/config.py`.
2. ~~Prepended to every agent prompt~~ — `app/core/prompt_context.py`, all agents, orchestrator `reviewer_context` state.
3. ~~README / `.env.sample`~~.

**Done when:** Env steers reviewer tone — **met** (restart API after changing env).

---

## Phase 2 — UX & trust

### 2A — Real analysis progress ✅
**Steps**
1. ~~Replace spinner-only UI with **SSE** endpoint reporting agent completion.~~ `POST /api/v1/analyze/stream`, `POST /api/v1/analyze/file/stream`.
2. ~~Map events to a checklist UI (Clarity ✓, Structure ✓, …).~~ — `App.tsx` pipeline checklist.

**Done when:** User sees which agents finished without opening logs — **met.**

### 2B — Section-scoped analysis ✅
**Steps**
1. ~~API: optional ``section_scope`` + ``section_hint`` on ``AnalysisRequest``.~~ — `app/api/models.py`; multipart form fields on file routes.
2. ~~Orchestrator: pass only selected slice to agents (before LLM windowing).~~ — `app/core/section_extract.py`, `prepare_orchestrator_state`.

**Done when:** Long papers can be reviewed per section without hitting limits — **met.**

### 2C — Redaction / privacy mode ✅
**Steps**
1. ~~Regex pass for emails, phones, grant IDs.~~ — `app/core/redaction.py`
2. ~~Toggle “strip before LLM”.~~ — `redact_before_llm` on `AnalysisRequest`; file routes use form field `redact_before_llm`; UI checkbox.

**Done when:** Sensitive patterns reduced before provider calls — **met.**

---

## Phase 3 — Collaboration & history

### 3A — Persistent history with DB
**Steps:** SQLite/Postgres on Render; migrations.

### 3B — Shareable read-only links
**Steps:** Opaque tokens; read-only JSON/HTML view.

### 3C — Compare two runs
**Steps:** Store snapshots; diff Markdown/JSON; optional LLM summary.

---

## Phase 4 — Deeper analysis

### 4A — Citation & consistency
**Steps:** Extract cites; flag vague claims; acronym expansion pass.

### 4B — Bibliography helper
**Steps:** `.bib` upload; suggested stubs *(human verifies)*.

### 4C — Reproducibility checklist agent
**Steps:** Structured JSON checklist in UI.

---

## Phase 5 — Platform & scale

### 5A — Rate limiting (slowapi / IP quotas).

### 5B — Multi-provider LLM (Groq / OpenAI / Anthropic).

### 5C — Async jobs + webhook for long analyses.

---

## Phase 6 — Quality engineering

### 6A — Golden-file tests for `parse_llm_json_dict`.

### 6B — Evaluation harness for prompts.

---

*Reorder based on audience: public deploy → prioritize Phase 5; lab internal → Phase 3.*
