from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .ids import DEFAULT_CATEGORY, normalize_category, source_id_from_path


@dataclass(frozen=True)
class PipelinePaths:
    """Centralizes filesystem paths used by the vocabulary pipeline."""

    content_root: Path = Path("content")
    sources_root: Path = Path("raw-data")
    db_name: str = "vocabulary.sqlite"

    def category_root(self, category: str) -> Path:
        return self.content_root / normalize_category(category)

    def raw_dir(self, category: str) -> Path:
        return self.category_root(category) / "raw"

    def normalized_dir(self, category: str) -> Path:
        return self.category_root(category) / "normalized"

    def review_dir(self, category: str) -> Path:
        return self.category_root(category) / "review"

    def lessons_dir(self, category: str) -> Path:
        return self.category_root(category) / "lessons"

    def report_dir(self, category: str) -> Path:
        return self.category_root(category) / "reports"

    def db_dir(self) -> Path:
        return self.content_root / "shared" / "db"

    def images_dir(self) -> Path:
        return self.content_root / "shared" / "images"

    def words_dir(self, category: str) -> Path:
        return self.category_root(category) / "words"

    def raw_output(self, source_path: Path, *, source_id: str | None = None, category: str | None = None) -> Path:
        selected_category = normalize_category(category)
        selected_source_id = source_id or source_id_from_path(source_path, category=selected_category)
        return self.raw_dir(selected_category) / f"{selected_source_id}.pages.json"

    def entries_output(
        self,
        raw_path: Path,
        *,
        category: str | None = None,
        source_id: str | None = None,
    ) -> Path:
        selected_category = self._category_from_raw(raw_path, category)
        selected_source_id = source_id or raw_path.name.removesuffix(".pages.json")
        return self.normalized_dir(selected_category) / f"{selected_source_id}.entries.jsonl"

    def review_markdown_output(
        self,
        entries_path: Path,
        *,
        category: str | None = None,
        source_id: str | None = None,
    ) -> Path:
        selected_category = self._category_from_entries(entries_path, category)
        selected_source_id = source_id or entries_path.name.removesuffix(".entries.jsonl")
        return self.review_dir(selected_category) / f"{selected_source_id}.review.md"

    def review_csv_output(
        self,
        entries_path: Path,
        *,
        category: str | None = None,
        source_id: str | None = None,
    ) -> Path:
        selected_category = self._category_from_entries(entries_path, category)
        selected_source_id = source_id or entries_path.name.removesuffix(".entries.jsonl")
        return self.review_dir(selected_category) / f"{selected_source_id}.review.csv"

    def report_output(
        self,
        raw_path: Path,
        *,
        category: str | None = None,
        source_id: str | None = None,
    ) -> Path:
        selected_category = self._category_from_raw(raw_path, category)
        selected_source_id = source_id or raw_path.name.removesuffix(".pages.json")
        return self.report_dir(selected_category) / f"{selected_source_id}.validation.json"

    def db_path(self, *, db_name: str | None = None) -> Path:
        name = db_name or self.db_name
        return self.db_dir() / name

    def category_for_raw(self, raw_path: Path, category: str | None = None) -> str:
        return self._category_from_raw(raw_path, category)

    def lesson_bundle_paths_for_raw(
        self,
        raw_path: Path,
        *,
        category: str | None = None,
        base_name: str = "all_lessons_extraction",
    ) -> tuple[Path, Path]:
        resolved_category = self.category_for_raw(raw_path, category)
        # Prefix with category so iOS app can find e.g. grade-4_all_lessons_extraction.json
        prefixed = f"{resolved_category}_{base_name}"
        return (
            self.lessons_output(resolved_category, f"{prefixed}.json"),
            self.lessons_output(resolved_category, f"{prefixed}.md"),
        )

    def lessons_output(self, category: str, file_name: str) -> Path:
        return self.lessons_dir(category) / file_name

    def words_output_path_for_raw(
        self,
        raw_path: Path,
        *,
        category: str | None = None,
    ) -> Path:
        resolved_category = self.category_for_raw(raw_path, category)
        return self.words_dir(resolved_category) / f"{resolved_category}_words.json"

    def _category_from_raw(self, raw_path: Path, category: str | None) -> str:
        if category:
            return normalize_category(category)
        parent = raw_path.parent
        if parent.name == "raw" and parent.parent:
            return normalize_category(parent.parent.name)
        if parent.name not in {"raw", "normalized", "review", "reports"}:
            return normalize_category(parent.name)
        return DEFAULT_CATEGORY

    def _category_from_entries(self, entries_path: Path, category: str | None) -> str:
        if category:
            return normalize_category(category)
        parent = entries_path.parent
        if parent.name == "normalized" and parent.parent:
            return normalize_category(parent.parent.name)
        if parent.name not in {"raw", "normalized", "review", "reports"}:
            return normalize_category(parent.name)
        return DEFAULT_CATEGORY
