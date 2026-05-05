import type { AnalysisResult } from "./types";

function safeFence(s: string): string {
  if (!s) return "";
  return s.replace(/```/g, "\\`\\`\\`");
}

function linesBlock(items: string[] | undefined, ordered = false): string {
  if (!items?.length) return "_None._\n";
  if (ordered) {
    return items.map((t, i) => `${i + 1}. ${t}`).join("\n") + "\n";
  }
  return items.map((t) => `- ${t}`).join("\n") + "\n";
}

/** Build a Markdown report from an analysis result (for download or sharing). */
export function analysisResultToMarkdown(
  result: AnalysisResult,
  options: { title?: string; generatedAt?: string } = {}
): string {
  const title = options.title ?? "Publication assistant — analysis report";
  const when = options.generatedAt ?? new Date().toISOString();
  const g = result.guardrails;
  const parts: string[] = [
    `# ${title}`,
    ``,
    `_Generated: ${when}_`,
    ``,
    `## Guardrails`,
    `- **Status:** ${g.status}`,
  ];
  if (g.reason) parts.push(`- **Reason:** ${g.reason}`);
  if (result.analysis_warnings?.length) {
    parts.push(``, `### Warnings`, ...result.analysis_warnings.map((w) => `- ${w}`));
  }
  parts.push(``);

  if (result.clarity) {
    parts.push(
      `## Clarity`,
      `### Improved text`,
      `\`\`\`text`,
      safeFence(result.clarity.improved_text),
      `\`\`\``,
      ``,
      `### Comments`,
      linesBlock(result.clarity.comments),
      ``
    );
  }

  if (result.structure) {
    parts.push(
      `## Structure`,
      `### Suggested outline`,
      linesBlock(result.structure.suggested_outline, true),
      ``,
      `### Section suggestions`,
      linesBlock(result.structure.section_suggestions),
      ``
    );
  }

  if (result.technical) {
    parts.push(
      `## Technical review`,
      `### Issues found`,
      linesBlock(result.technical.issues_found),
      ``,
      `### Suggestions`,
      linesBlock(result.technical.suggestions),
      ``,
      `_Model confidence: ${(result.technical.overall_confidence * 100).toFixed(0)}%_`,
      ``
    );
  }

  if (result.visuals) {
    const sugg = result.visuals.suggestions;
    let vis = `## Visual suggestions\n\n`;
    if (sugg?.length) {
      for (const v of sugg) {
        vis += `### ${v.title} _(${v.type})_\n\n${v.description}\n\n`;
      }
    } else {
      vis += "_No structured suggestions._\n\n";
    }
    vis += `### Formatting tips\n\n${linesBlock(result.visuals.formatting_tips)}`;
    parts.push(vis, ``);
  }

  if (result.summary) {
    parts.push(
      `## Summary`,
      `### Abstract`,
      result.summary.summary,
      ``,
      `### Key contributions`,
      linesBlock(result.summary.key_contributions, true),
      ``
    );
  }

  if (result.tags) {
    parts.push(
      `## Titles & tags`,
      `### Title suggestions`,
      linesBlock(result.tags.title_suggestions, true),
      ``,
      `### Tags`,
      result.tags.tags.map((t) => `- \`${t}\``).join("\n") + "\n",
      ``
    );
  }

  return parts.join("\n");
}

export function downloadTextFile(filename: string, content: string, mime = "text/markdown;charset=utf-8") {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
