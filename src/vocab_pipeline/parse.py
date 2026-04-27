from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .ids import DEFAULT_CATEGORY, normalize_category, normalize_term, stable_entry_id
from .json_io import read_json, write_jsonl


ENTRY_SCHEMA_VERSION = "vocabulary-entry.v1"
GENERIC_PARSER_VERSION = "generic-line-parser.v1"
DEFAULT_PARSER_PROFILE = "generic"

INLINE_ENTRY_RE = re.compile(
    r"^(?P<term>[A-Za-z][A-Za-z '\u2019\-]{1,80})\s*(?:--|-|:|\u2014|\u2013)\s*(?P<definition>\S.+)$"
)
TERM_ONLY_RE = re.compile(r"^[A-Za-z][A-Za-z '\u2019\-]{1,50}$")


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


def parse_page_text(text: str, parser_profile: str = DEFAULT_PARSER_PROFILE) -> list[dict[str, str]]:
    parser_version_for_profile(parser_profile)
    lines = _clean_lines(text)
    entries: list[dict[str, str]] = []
    pending_term: str | None = None
    pending_definition: list[str] = []

    def flush_pending() -> None:
        nonlocal pending_term, pending_definition
        if pending_term and pending_definition:
            entries.append(
                {
                    "term": pending_term,
                    "definition": " ".join(pending_definition).strip(),
                    "raw_entry_text": "\n".join([pending_term, *pending_definition]),
                }
            )
        pending_term = None
        pending_definition = []

    for line in lines:
        inline_match = INLINE_ENTRY_RE.match(line)
        if inline_match:
            flush_pending()
            entries.append(
                {
                    "term": inline_match.group("term").strip(),
                    "definition": inline_match.group("definition").strip(),
                    "raw_entry_text": line,
                }
            )
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
                    "definition": definition,
                    "part_of_speech": None,
                    "root_or_origin": None,
                    "example": None,
                    "section": None,
                    "category": category,
                    "source_id": source_id,
                    "source_page": page_number,
                    "source_order": source_order,
                    "raw_entry_text": parsed_entry["raw_entry_text"],
                    "parser_profile": parser_profile,
                    "parser_version": parser_version,
                    "review_status": "needs_review",
                    "warnings": warnings,
                }
            )
    return records


def default_entries_output(raw_path: Path, data_root: Path = Path("data"), category: str | None = None) -> Path:
    source_id = raw_path.name.removesuffix(".pages.json")
    if category:
        selected_category = normalize_category(category)
    elif raw_path.parent.name == "raw":
        selected_category = DEFAULT_CATEGORY
    else:
        selected_category = normalize_category(raw_path.parent.name)
    normalized_root = data_root / "normalized"
    if selected_category != DEFAULT_CATEGORY:
        normalized_root = normalized_root / selected_category
    return normalized_root / f"{source_id}.entries.jsonl"


def parse_raw_file(
    raw_path: Path,
    output_path: Path | None = None,
    parser_profile: str = DEFAULT_PARSER_PROFILE,
) -> tuple[Path, int]:
    raw_payload = read_json(raw_path)
    category = raw_payload.get("source", {}).get("category")
    selected_output_path = output_path or default_entries_output(raw_path, category=str(category or DEFAULT_CATEGORY))
    records = parse_raw_payload(raw_payload, parser_profile=parser_profile)
    count = write_jsonl(selected_output_path, records)
    return selected_output_path, count
