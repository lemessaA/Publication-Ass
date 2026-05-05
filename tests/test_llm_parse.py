import json

from app.core.llm_parse import clean_comment_lines, parse_llm_json_dict, split_fallback_paragraphs


def test_parse_fenced_json():
    raw = """Here you go:
```json
{"improved_text": "Hi", "comments": ["a"]}
```
"""
    d = parse_llm_json_dict(raw)
    assert d is not None
    assert d["improved_text"] == "Hi"


def test_parse_brace_substring():
    raw = 'Preamble text {"x": 1, "y": "z"} trailing'
    d = parse_llm_json_dict(raw)
    assert d == {"x": 1, "y": "z"}


def test_parse_dict_passthrough():
    assert parse_llm_json_dict({"a": 1}) == {"a": 1}


def test_split_fallback():
    t = "First block here.\n\nSecond block there.\n\n" + ("x" * 2000)
    out = split_fallback_paragraphs(t, max_items=3, max_chars_each=100)
    assert len(out) <= 3
    assert all(len(s) <= 150 for s in out)


def test_clean_comments_drops_chatter():
    c = clean_comment_lines(
        [
            "Here is a good fix.",
            "Tighten the related work section for clarity.",
        ]
    )
    assert any("Tighten" in x for x in c)
    assert not any("Here is" in x for x in c)
