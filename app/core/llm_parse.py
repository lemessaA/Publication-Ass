"""Extract structured JSON from LLM replies that may include markdown fences or chatter."""

from __future__ import annotations

import json
import re
from typing import Any


_JSON_FENCE_START = re.compile(r"^\s*```(?:json)?\s*", re.IGNORECASE | re.MULTILINE)
_JSON_FENCE_END = re.compile(r"\s*```\s*$", re.MULTILINE)


JSON_ONLY_SUFFIX = (
    "\n\nOUTPUT RULES (mandatory):\n"
    "- Return a single JSON object only.\n"
    "- Do not use markdown code fences (no ```).\n"
    "- Do not include explanations, apologies, or text before or after the JSON.\n"
)


def parse_llm_json_dict(content: Any) -> dict[str, Any] | None:
    """Best-effort parse of a JSON object from model output."""
    if content is None:
        return None
    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        content = str(content)

    text = content.strip()
    if not text:
        return None

    # Strip ```json ... ``` wrappers if present
    text = _JSON_FENCE_START.sub("", text, count=1)
    text = _JSON_FENCE_END.sub("", text, count=1)
    text = text.strip()

    for candidate in _json_candidates(text):
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return None


def _json_candidates(text: str) -> list[str]:
    """Try whole string, then substring from first '{' to last '}'."""
    candidates = [text.strip()]
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start : end + 1])
    return candidates


def truncate_plain(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    if max_chars < 2:
        return "…"
    prefix = text[: max_chars - 1]
    if " " in prefix:
        return prefix.rsplit(" ", 1)[0] + "…"
    return prefix + "…"


def split_fallback_paragraphs(text: str, max_items: int, max_chars_each: int) -> list[str]:
    """Turn a noisy prose fallback into short bullet-sized chunks."""
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"\n\s*\n+", text)
    out: list[str] = []
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip()
        if len(p) < 12:
            continue
        if _looks_like_noise_line(p):
            continue
        out.append(truncate_plain(p, max_chars_each))
        if len(out) >= max_items:
            break
    return out


_NOISE_START = re.compile(
    r"^(here\s+(is|are)|sure[,!]|certainly|certainly[,!]|below\s+(is|you)|"
    r"as\s+requested|i\s+(have|'ve)\s+(prepared|included)|json\s*:)",
    re.IGNORECASE,
)


def _looks_like_noise_line(line: str) -> bool:
    s = line.strip()
    if len(s) < 20 and "```" in s:
        return True
    return bool(_NOISE_START.match(s))


def clean_comment_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    for line in lines:
        t = re.sub(r"\s+", " ", str(line)).strip()
        if not t or _looks_like_noise_line(t):
            continue
        cleaned.append(truncate_plain(t, 800))
    return cleaned
