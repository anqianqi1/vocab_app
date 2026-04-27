from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .ids import DEFAULT_CATEGORY, normalize_category
from .json_io import read_json, read_jsonl, write_json


def validate_payload(raw_payload: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    pages = raw_payload.get("pages", [])
    empty_pages = [page.get("page") for page in pages if not str(page.get("text") or "").strip()]
    source = raw_payload.get("source", {})
    source_category = str(source.get("category") or DEFAULT_CATEGORY)
    source_warnings = list(source.get("warnings") or [])

    term_counts = Counter(str(entry.get("normalized_term") or "") for entry in entries)
    duplicate_terms = sorted(term for term, count in term_counts.items() if term and count > 1)
    category_mismatch_ids = [
        entry.get("id")
        for entry in entries
        if str(entry.get("category") or DEFAULT_CATEGORY) != source_category
    ]

    missing_term_ids = [entry.get("id") for entry in entries if not str(entry.get("term") or "").strip()]
    missing_definition_ids = [entry.get("id") for entry in entries if not str(entry.get("definition") or "").strip()]
    warning_counts: dict[str, int] = defaultdict(int)
    category_counts: dict[str, int] = defaultdict(int)
    parser_profile_counts: dict[str, int] = defaultdict(int)
    for entry in entries:
        category_counts[str(entry.get("category") or DEFAULT_CATEGORY)] += 1
        parser_profile_counts[str(entry.get("parser_profile") or "unknown")] += 1
        for warning in entry.get("warnings") or []:
            warning_counts[str(warning)] += 1

    status = "ok"
    if source_warnings or not entries or missing_term_ids or missing_definition_ids or category_mismatch_ids:
        status = "needs_attention"

    return {
        "schema_version": "validation-report.v1",
        "status": status,
        "source": source,
        "page_count": len(pages),
        "empty_page_count": len(empty_pages),
        "empty_pages": empty_pages,
        "entry_count": len(entries),
        "entry_category_counts": dict(sorted(category_counts.items())),
        "parser_profile_counts": dict(sorted(parser_profile_counts.items())),
        "category_mismatch_ids": category_mismatch_ids,
        "duplicate_normalized_terms": duplicate_terms,
        "missing_term_ids": missing_term_ids,
        "missing_definition_ids": missing_definition_ids,
        "entry_warning_counts": dict(sorted(warning_counts.items())),
        "recommendations": build_recommendations(source_warnings, pages, entries, category_mismatch_ids),
    }


def build_recommendations(
    source_warnings: list[str],
    pages: list[dict[str, Any]],
    entries: list[dict[str, Any]],
    category_mismatch_ids: list[Any] | None = None,
) -> list[str]:
    recommendations: list[str] = []
    if "no_extractable_text_detected" in source_warnings:
        recommendations.append(
            "No extractable text was detected. Try OCR or a positional extraction engine before parsing vocabulary."
        )
    if pages and not entries:
        recommendations.append(
            "No entries were parsed. Inspect data/raw output and update parsing rules after confirming text extraction quality."
        )
    if any(not str(entry.get("definition") or "").strip() for entry in entries):
        recommendations.append("Some entries are missing definitions and should be reviewed manually.")
    if category_mismatch_ids:
        recommendations.append("Some entries have a different category than their raw source metadata.")
    if not recommendations:
        recommendations.append("Review random entries against the source PDF before packaging the data for apps.")
    return recommendations


def default_report_output(
    raw_path: Path,
    reports_root: Path = Path("reports"),
    category: str | None = None,
) -> Path:
    source_id = raw_path.name.removesuffix(".pages.json")
    if category:
        selected_category = normalize_category(category)
    elif raw_path.parent.name == "raw":
        selected_category = DEFAULT_CATEGORY
    else:
        selected_category = normalize_category(raw_path.parent.name)
    report_root = reports_root
    if selected_category != DEFAULT_CATEGORY:
        report_root = report_root / selected_category
    return report_root / f"{source_id}.validation.json"


def validate_files(raw_path: Path, entries_path: Path | None = None, output_path: Path | None = None) -> Path:
    raw_payload = read_json(raw_path)
    entries = read_jsonl(entries_path) if entries_path else []
    category = raw_payload.get("source", {}).get("category")
    selected_output_path = output_path or default_report_output(raw_path, category=str(category or DEFAULT_CATEGORY))
    report = validate_payload(raw_payload, entries)
    write_json(selected_output_path, report)
    return selected_output_path
