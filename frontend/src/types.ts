export type ContentType = "plain_text" | "markdown" | "latex";

export interface DocumentInput {
  content: string;
  content_type?: ContentType;
  source?: "text" | "file";
  filename?: string | null;
}

export interface ClarityFeedback {
  improved_text: string;
  comments: string[];
}

export interface StructureFeedback {
  suggested_outline: string[];
  section_suggestions: string[];
}

export interface TechnicalFeedback {
  issues_found: string[];
  suggestions: string[];
  overall_confidence: number;
}

export interface VisualSuggestion {
  title: string;
  description: string;
  type: string;
}

export interface VisualFeedback {
  suggestions: VisualSuggestion[];
  formatting_tips: string[];
}

export interface SummaryFeedback {
  summary: string;
  key_contributions: string[];
}

export interface TagFeedback {
  title_suggestions: string[];
  tags: string[];
}

export type GuardrailStatus = "ok" | "rejected";

export interface GuardrailResult {
  status: GuardrailStatus;
  reason?: string | null;
  details?: Record<string, unknown> | null;
}

export interface AnalysisResult {
  clarity?: ClarityFeedback | null;
  structure?: StructureFeedback | null;
  technical?: TechnicalFeedback | null;
  visuals?: VisualFeedback | null;
  summary?: SummaryFeedback | null;
  tags?: TagFeedback | null;
  guardrails: GuardrailResult;
}

export interface AnalysisRequest {
  document: DocumentInput;
  run_clarity?: boolean;
  run_structure?: boolean;
  run_technical?: boolean;
  run_visuals?: boolean;
  run_summary?: boolean;
  run_tags?: boolean;
}

export interface AnalysisResponse {
  id: string;
  created_at: string;
  request: AnalysisRequest;
  result: AnalysisResult;
}

