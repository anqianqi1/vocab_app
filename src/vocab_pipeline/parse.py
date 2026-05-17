from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .ids import DEFAULT_CATEGORY, normalize_category, normalize_term, stable_entry_id
from .json_io import read_json, write_jsonl
from .paths import PipelinePaths


ENTRY_SCHEMA_VERSION = "vocabulary-entry.v1"
GENERIC_PARSER_VERSION = "generic-line-parser.v1"
DEFAULT_PARSER_PROFILE = "generic"

INLINE_ENTRY_RE = re.compile(
    r"^(?P<term>[A-Za-z][A-Za-z '\u2019\-]{1,80})\s*(?:--|-|:|\u2014|\u2013)\s*(?P<definition>\S.+)$"
)
TERM_ONLY_RE = re.compile(r"^[A-Za-z][A-Za-z '\u2019\-]{1,50}$")
SECTION_HEADING_RE = re.compile(r"^lesson\s+\d+[:\-–—]?\s*(.+)$", re.IGNORECASE)
NUMBERED_ENTRY_RE = re.compile(
    r"^(?:\d+)\.\s*(?P<term>[A-Za-z][A-Za-z '\u2019\-]+)(?:\s*\([^)]*\))?$"
)
RELATED_WORDS_START_RE = re.compile(r"^(Familiar Words|Challenge Words)\b", re.IGNORECASE)
KEY_WORDS_HEADER_RE = re.compile(r"^Key Words\s*$", re.IGNORECASE)


def _clean_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if line:
            lines.append(line)
    return lines


def _looks_like_term(line: str) -> bool:
    if not TERM_ONLY_RE.match(line):
        return False
    words = line.split()
    if len(words) > 4:
        return False
    return line.istitle() or line.isupper() or len(words) == 1


def available_parser_profiles() -> list[str]:
    return [DEFAULT_PARSER_PROFILE]


def parser_version_for_profile(parser_profile: str) -> str:
    if parser_profile != DEFAULT_PARSER_PROFILE:
        raise ValueError(
            f"Unknown parser profile {parser_profile!r}. Available profiles: {', '.join(available_parser_profiles())}"
        )
    return GENERIC_PARSER_VERSION


def _extract_example_sentence(definition_lines: list[str]) -> str | None:
    for line in definition_lines:
        sentence = line.strip()
        if sentence and sentence[0].isupper() and sentence.endswith("."):
            return sentence
    return None


def parse_page_text(text: str, parser_profile: str = DEFAULT_PARSER_PROFILE) -> list[dict[str, Any]]:
    parser_version_for_profile(parser_profile)
    lines = _clean_lines(text)
    entries: list[dict[str, str]] = []
    pending_term: str | None = None
    pending_definition: list[str] = []
    pending_related_terms: list[str] = []
    current_section: str | None = None
    current_related_words: list[str] = []
    in_related_block = False

    def flush_pending() -> None:
        nonlocal pending_term, pending_definition, pending_related_terms
        if pending_term and pending_definition:
            example = _extract_example_sentence(pending_definition[1:]) if len(pending_definition) > 1 else None
            entry: dict[str, str] = {
                "term": pending_term,
                "definition": pending_definition[0].strip(),
                "raw_entry_text": "\n".join([pending_term, *pending_definition]),
            }
            if current_section:
                entry["section"] = current_section
            if pending_related_terms:
                entry["related_terms"] = pending_related_terms.copy()
            if example:
                entry["example"] = example
            entries.append(entry)
        pending_term = None
        pending_definition = []
        pending_related_terms = []

    for line in lines:
        if not line:
            in_related_block = False
            continue

        section_match = SECTION_HEADING_RE.match(line)
        if section_match:
            current_section = section_match.group(1).strip().title()
            continue

        if KEY_WORDS_HEADER_RE.match(line):
            in_related_block = False
            continue

        related_match = RELATED_WORDS_START_RE.match(line)
        if related_match:
            in_related_block = True
            current_related_words = []
            continue

        if in_related_block and line and not line.endswith(":"):
            words = [word.strip() for word in re.split(r"[\s,]+", line) if word.strip()]
            current_related_words.extend(words)
            pending_related_terms = current_related_words.copy()
            continue

        inline_match = INLINE_ENTRY_RE.match(line)
        if inline_match:
            flush_pending()
            entries.append(
                {
                    "term": inline_match.group("term").strip(),
                    "definition": inline_match.group("definition").strip(),
                    "raw_entry_text": line,
                    "section": current_section or "",
                    "related_terms": pending_related_terms.copy() if pending_related_terms else [],
                }
            )
            continue

        numbered_match = NUMBERED_ENTRY_RE.match(line)
        if numbered_match:
            flush_pending()
            pending_term = numbered_match.group("term").strip()
            pending_definition = []
            continue

        if _looks_like_term(line):
            flush_pending()
            pending_term = line
            continue

        if pending_term:
            pending_definition.append(line)

    flush_pending()
    return entries


def parse_raw_payload(raw_payload: dict[str, Any], parser_profile: str = DEFAULT_PARSER_PROFILE) -> list[dict[str, Any]]:
    parser_version = parser_version_for_profile(parser_profile)
    source = raw_payload.get("source", {})
    source_id = str(source.get("source_id") or "unknown-source")
    category = normalize_category(str(source.get("category") or DEFAULT_CATEGORY))
    records: list[dict[str, Any]] = []
    source_order = 0

    for page in raw_payload.get("pages", []):
        page_number = int(page.get("page", 0))
        text = str(page.get("text") or "")
        for parsed_entry in parse_page_text(text, parser_profile=parser_profile):
            source_order += 1
            term = parsed_entry["term"]
            definition = parsed_entry["definition"]
            warnings: list[str] = []
            if not term.strip():
                warnings.append("missing_term")
            if not definition.strip():
                warnings.append("missing_definition")
            if len(definition.strip()) < 8:
                warnings.append("short_definition")

            records.append(
                {
                    "schema_version": ENTRY_SCHEMA_VERSION,
                    "id": stable_entry_id(source_id, page_number, source_order, term),
                    "term": term,
                    "normalized_term": normalize_term(term),
                    "word_type": None,
                    "definition": definition,
                    "part_of_speech": None,
                    "root_or_origin": None,
                    "example": parsed_entry.get("example"),
                    "section": parsed_entry.get("section"),
                    "category": category,
                    "source_id": source_id,
                    "source_page": page_number,
                    "source_order": source_order,
                    "raw_entry_text": parsed_entry["raw_entry_text"],
                    "parser_profile": parser_profile,
                    "parser_version": parser_version,
                    "review_status": "needs_review",
                    "example_sentence": parsed_entry.get("example_sentence"),
                    "warnings": warnings,
                    "related_terms": parsed_entry.get("related_terms", []),
                }
            )
    return records


def default_entries_output(raw_path: Path, content_root: Path = Path("content"), category: str | None = None) -> Path:
    paths = PipelinePaths(content_root=content_root)
    return paths.entries_output(raw_path, category=category)


def parse_raw_file(
    raw_path: Path,
    output_path: Path | None = None,
    word_type: str | None = None,
    parser_profile: str = DEFAULT_PARSER_PROFILE,
) -> tuple[Path, int]:
    raw_payload = read_json(raw_path)
    category = raw_payload.get("source", {}).get("category")
    selected_output_path = output_path or default_entries_output(raw_path, category=str(category or DEFAULT_CATEGORY))
    records = parse_raw_payload(raw_payload, parser_profile=parser_profile)
    count = write_jsonl(selected_output_path, records)
    return selected_output_path, count
