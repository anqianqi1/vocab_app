from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from .db import build_database
from .extract import extract_to_file
from .ids import DEFAULT_CATEGORY, normalize_category, source_id_from_path
from .parse import DEFAULT_PARSER_PROFILE, parse_raw_file
from .paths import PipelinePaths
from .review import write_review_files
from .validate import validate_files


@dataclass(frozen=True)
class PipelineResult:
    source_id: str
    category: str
    parser_profile: str
    source_path: Path
    raw_path: Path
    entries_path: Path
    review_markdown_path: Path
    review_csv_path: Path
    validation_report_path: Path
    db_path: Path | None
    entry_count: int
    fts_enabled: bool | None

    def as_summary(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "category": self.category,
            "parser_profile": self.parser_profile,
            "pdf_path": str(self.source_path),
            "raw_path": str(self.raw_path),
            "entries_path": str(self.entries_path),
            "review_markdown_path": str(self.review_markdown_path),
            "review_csv_path": str(self.review_csv_path),
            "validation_report_path": str(self.validation_report_path),
            "db_path": str(self.db_path) if self.db_path else None,
            "entry_count": self.entry_count,
            "fts_enabled": self.fts_enabled,
            "next_step": None
            if self.entry_count
            else "No entries were parsed. Inspect the validation report and run OCR or a stronger extraction engine before building the app database.",
        }


class PipelineRunner:
    """Coordinates extract → parse → review → validate → database steps."""

    def __init__(self, paths: PipelinePaths | None = None) -> None:
        self.paths = paths or PipelinePaths()

    def run_all(
        self,
        source_path: Path,
        *,
        category: str = DEFAULT_CATEGORY,
        source_id: str | None = None,
        source_title: str | None = None,
        parser_profile: str = DEFAULT_PARSER_PROFILE,
        raw_path: Path | None = None,
        entries_path: Path | None = None,
        review_markdown_path: Path | None = None,
        review_csv_path: Path | None = None,
        validation_report_path: Path | None = None,
        db_path: Path | None = None,
        allow_empty_db: bool = False,
    ) -> PipelineResult:
        selected_category = normalize_category(category)
        selected_source_id = source_id or source_id_from_path(source_path, category=selected_category)

        resolved_raw_path = raw_path or self.paths.raw_output(
            source_path,
            source_id=selected_source_id,
            category=selected_category,
        )
        resolved_entries_path = entries_path or self.paths.entries_output(
            resolved_raw_path,
            category=selected_category,
            source_id=selected_source_id,
        )
        resolved_review_markdown_path = review_markdown_path or self.paths.review_markdown_output(
            resolved_entries_path,
            category=selected_category,
            source_id=selected_source_id,
        )
        resolved_review_csv_path = review_csv_path or self.paths.review_csv_output(
            resolved_entries_path,
            category=selected_category,
            source_id=selected_source_id,
        )
        resolved_report_path = validation_report_path or self.paths.report_output(
            resolved_raw_path,
            category=selected_category,
            source_id=selected_source_id,
        )
        resolved_db_path = db_path or self.paths.db_path()

        extract_to_file(
            source_path,
            output_path=resolved_raw_path,
            source_id=selected_source_id,
            category=selected_category,
            source_title=source_title,
        )
        _, entry_count = parse_raw_file(
            resolved_raw_path,
            output_path=resolved_entries_path,
            parser_profile=parser_profile,
        )
        write_review_files(
            resolved_entries_path,
            markdown_path=resolved_review_markdown_path,
            csv_path=resolved_review_csv_path,
            category=selected_category,
        )
        validate_files(
            resolved_raw_path,
            entries_path=resolved_entries_path,
            output_path=resolved_report_path,
        )

        db_summary: dict[str, Any] | None = None
        if entry_count or allow_empty_db:
            db_summary = build_database(
                resolved_raw_path,
                resolved_entries_path,
                db_path=resolved_db_path,
            )

        return PipelineResult(
            source_id=selected_source_id,
            category=selected_category,
            parser_profile=parser_profile,
            source_path=source_path,
            raw_path=resolved_raw_path,
            entries_path=resolved_entries_path,
            review_markdown_path=resolved_review_markdown_path,
            review_csv_path=resolved_review_csv_path,
            validation_report_path=resolved_report_path,
            db_path=resolved_db_path if db_summary else None,
            entry_count=entry_count,
            fts_enabled=db_summary["fts_enabled"] if db_summary else None,
        )

    def run_batch(
        self,
        source_paths: Sequence[Path],
        *,
        category: str | None = None,
        category_from_parent: bool = False,
        parser_profile: str = DEFAULT_PARSER_PROFILE,
        db_path: Path | None = None,
        allow_empty_db: bool = False,
    ) -> list[PipelineResult]:
        results: list[PipelineResult] = []
        for source_path in source_paths:
            selected_category = self._category_for_batch_item(
                source_path,
                explicit_category=category,
                category_from_parent=category_from_parent,
            )
            results.append(
                self.run_all(
                    source_path,
                    category=selected_category,
                    parser_profile=parser_profile,
                    db_path=db_path,
                    allow_empty_db=allow_empty_db,
                )
            )
        return results

    def _category_for_batch_item(
        self,
        source_path: Path,
        *,
        explicit_category: str | None,
        category_from_parent: bool,
    ) -> str:
        if explicit_category:
            return normalize_category(explicit_category)
        if category_from_parent:
            return normalize_category(source_path.parent.name)
        return DEFAULT_CATEGORY
