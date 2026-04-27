from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from .ids import DEFAULT_CATEGORY, normalize_category, sha256_file, source_id_from_path
from .json_io import write_json


RAW_SCHEMA_VERSION = "raw-pages.v1"


def extract_pdf_pages(
    pdf_path: Path,
    source_id: str | None = None,
    category: str | None = None,
    source_title: str | None = None,
) -> dict[str, Any]:
    resolved_pdf_path = pdf_path.resolve()
    if not resolved_pdf_path.exists():
        raise FileNotFoundError(resolved_pdf_path)

    reader = PdfReader(str(resolved_pdf_path))
    selected_category = normalize_category(category)
    selected_source_id = source_id or source_id_from_path(resolved_pdf_path, category=selected_category)
    pages: list[dict[str, Any]] = []

    for page_index, page in enumerate(reader.pages, start=1):
        extracted_text = page.extract_text() or ""
        cleaned_text = extracted_text.replace("\x00", "")
        warnings: list[str] = []
        if not cleaned_text.strip():
            warnings.append("empty_text")
        pages.append(
            {
                "page": page_index,
                "text": cleaned_text,
                "char_count": len(cleaned_text),
                "warnings": warnings,
            }
        )

    nonempty_pages = sum(1 for page in pages if page["char_count"] > 0)
    source_warnings: list[str] = []
    if nonempty_pages == 0:
        source_warnings.append("no_extractable_text_detected")

    return {
        "schema_version": RAW_SCHEMA_VERSION,
        "source": {
            "source_id": selected_source_id,
            "category": selected_category,
            "source_title": source_title or resolved_pdf_path.stem.replace("_", " "),
            "file_name": resolved_pdf_path.name,
            "file_path": str(resolved_pdf_path),
            "file_sha256": sha256_file(resolved_pdf_path),
            "page_count": len(reader.pages),
            "extracted_at": datetime.now(UTC).isoformat(),
            "extraction_engine": "pypdf",
            "warnings": source_warnings,
        },
        "pages": pages,
    }


def default_raw_output(
    pdf_path: Path,
    data_root: Path = Path("data"),
    source_id: str | None = None,
    category: str | None = None,
) -> Path:
    selected_category = normalize_category(category)
    selected_source_id = source_id or source_id_from_path(pdf_path, category=selected_category)
    raw_root = data_root / "raw"
    if selected_category != DEFAULT_CATEGORY:
        raw_root = raw_root / selected_category
    return raw_root / f"{selected_source_id}.pages.json"


def extract_to_file(
    pdf_path: Path,
    output_path: Path | None = None,
    source_id: str | None = None,
    category: str | None = None,
    source_title: str | None = None,
) -> Path:
    selected_output_path = output_path or default_raw_output(pdf_path, source_id=source_id, category=category)
    payload = extract_pdf_pages(pdf_path, source_id=source_id, category=category, source_title=source_title)
    write_json(selected_output_path, payload)
    return selected_output_path
