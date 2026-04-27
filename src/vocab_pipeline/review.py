from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .ids import DEFAULT_CATEGORY, normalize_category
from .json_io import ensure_parent, read_jsonl


def _category_from_entries_path(entries_path: Path) -> str:
    if entries_path.parent.name == "normalized":
        return DEFAULT_CATEGORY
    return normalize_category(entries_path.parent.name)


def default_review_markdown_output(
    entries_path: Path,
    data_root: Path = Path("data"),
    category: str | None = None,
) -> Path:
    source_id = entries_path.name.removesuffix(".entries.jsonl")
    selected_category = normalize_category(category or _category_from_entries_path(entries_path))
    review_root = data_root / "review"
    if selected_category != DEFAULT_CATEGORY:
        review_root = review_root / selected_category
    return review_root / f"{source_id}.review.md"


def default_review_csv_output(
    entries_path: Path,
    data_root: Path = Path("data"),
    category: str | None = None,
) -> Path:
    source_id = entries_path.name.removesuffix(".entries.jsonl")
    selected_category = normalize_category(category or _category_from_entries_path(entries_path))
    review_root = data_root / "review"
    if selected_category != DEFAULT_CATEGORY:
        review_root = review_root / selected_category
    return review_root / f"{source_id}.review.csv"


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
