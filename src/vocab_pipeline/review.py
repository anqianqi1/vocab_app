from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .ids import DEFAULT_CATEGORY
from .json_io import ensure_parent, read_jsonl
from .paths import PipelinePaths


def default_review_markdown_output(
    entries_path: Path,
    content_root: Path = Path("content"),
    category: str | None = None,
) -> Path:
    paths = PipelinePaths(content_root=content_root)
    return paths.review_markdown_output(entries_path, category=category)


def default_review_csv_output(
    entries_path: Path,
    content_root: Path = Path("content"),
    category: str | None = None,
) -> Path:
    paths = PipelinePaths(content_root=content_root)
    return paths.review_csv_output(entries_path, category=category)


def write_review_markdown(path: Path, entries: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as file_handle:
        file_handle.write("# Vocabulary Extraction Review\n\n")
        file_handle.write(f"Entries: {len(entries)}\n\n")
        if not entries:
            file_handle.write(
                "No vocabulary entries were parsed. If the raw extraction has empty pages, "
                "this PDF likely needs OCR or a different extraction engine.\n"
            )
            return

        for entry in entries:
            file_handle.write(f"## {entry.get('term') or '[missing term]'}\n\n")
            file_handle.write(f"- ID: `{entry.get('id')}`\n")
            file_handle.write(f"- Category: `{entry.get('category') or DEFAULT_CATEGORY}`\n")
            if entry.get("section"):
                file_handle.write(f"- Section: `{entry.get('section')}`\n")
            file_handle.write(f"- Source: `{entry.get('source_id')}` page {entry.get('source_page')}\n")
            file_handle.write(f"- Parser profile: `{entry.get('parser_profile') or 'unknown'}`\n")
            file_handle.write(f"- Parser version: `{entry.get('parser_version') or 'unknown'}`\n")
            file_handle.write(f"- Review status: `{entry.get('review_status')}`\n")
            if entry.get("example"):
                file_handle.write(f"- Example: `{entry.get('example')}`\n")
            related_terms = entry.get("related_terms") or []
            if related_terms:
                file_handle.write(f"- Related terms: `{', '.join(related_terms)}`\n")
            warnings = entry.get("warnings") or []
            if warnings:
                file_handle.write(f"- Warnings: `{', '.join(warnings)}`\n")
            file_handle.write("\n")
            file_handle.write("**Definition**\n\n")
            file_handle.write(f"{entry.get('definition') or '[missing definition]'}\n\n")
            file_handle.write("**Raw Entry Text**\n\n")
            file_handle.write("```text\n")
            file_handle.write(str(entry.get("raw_entry_text") or ""))
            file_handle.write("\n```\n\n")


def write_review_csv(path: Path, entries: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    fieldnames = [
        "id",
        "term",
        "definition",
        "example",
        "related_terms",
        "section",
        "category",
        "source_id",
        "source_page",
        "source_order",
        "parser_profile",
        "parser_version",
        "review_status",
        "warnings",
        "raw_entry_text",
    ]
    with path.open("w", encoding="utf-8", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            row = {fieldname: entry.get(fieldname) for fieldname in fieldnames}
            row["warnings"] = ";".join(entry.get("warnings") or [])
            row["related_terms"] = ";".join(entry.get("related_terms") or [])
            writer.writerow(row)


def write_review_files(
    entries_path: Path,
    markdown_path: Path | None = None,
    csv_path: Path | None = None,
    category: str | None = None,
) -> tuple[Path, Path, int]:
    entries = read_jsonl(entries_path)
    selected_markdown_path = markdown_path or default_review_markdown_output(entries_path, category=category)
    selected_csv_path = csv_path or default_review_csv_output(entries_path, category=category)
    write_review_markdown(selected_markdown_path, entries)
    write_review_csv(selected_csv_path, entries)
    return selected_markdown_path, selected_csv_path, len(entries)
