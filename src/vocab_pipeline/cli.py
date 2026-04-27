from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from .db import build_database, default_db_output
from .extract import default_raw_output, extract_to_file
from .ids import DEFAULT_CATEGORY, normalize_category, source_id_from_path
from .parse import DEFAULT_PARSER_PROFILE, available_parser_profiles, default_entries_output, parse_raw_file
from .review import default_review_csv_output, default_review_markdown_output, write_review_files
from .validate import default_report_output, validate_files


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def discover_pdf_paths(paths: list[str]) -> list[Path]:
    pdf_paths: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            pdf_paths.extend(sorted(child for child in path.rglob("*") if child.is_file() and child.suffix.lower() == ".pdf"))
            continue
        if path.is_file() and path.suffix.lower() == ".pdf":
            pdf_paths.append(path)
            continue
        raise FileNotFoundError(f"Expected a PDF file or directory containing PDFs: {path}")
    return pdf_paths


def category_for_pdf(pdf_path: Path, args: argparse.Namespace) -> str:
    if getattr(args, "category", None):
        return normalize_category(args.category)
    if getattr(args, "category_from_parent", False):
        return normalize_category(pdf_path.parent.name)
    return DEFAULT_CATEGORY


def run_pdf_pipeline(
    pdf_path: Path,
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
) -> dict[str, Any]:
    selected_category = normalize_category(category)
    selected_source_id = source_id or source_id_from_path(pdf_path, category=selected_category)
    selected_raw_path = raw_path or default_raw_output(
        pdf_path,
        source_id=selected_source_id,
        category=selected_category,
    )
    selected_entries_path = entries_path or default_entries_output(selected_raw_path, category=selected_category)
    selected_review_markdown_path = review_markdown_path or default_review_markdown_output(
        selected_entries_path,
        category=selected_category,
    )
    selected_review_csv_path = review_csv_path or default_review_csv_output(
        selected_entries_path,
        category=selected_category,
    )
    selected_validation_report_path = validation_report_path or default_report_output(
        selected_raw_path,
        category=selected_category,
    )
    selected_db_path = db_path or default_db_output()

    extract_to_file(
        pdf_path,
        output_path=selected_raw_path,
        source_id=selected_source_id,
        category=selected_category,
        source_title=source_title,
    )
    _, entry_count = parse_raw_file(
        selected_raw_path,
        output_path=selected_entries_path,
        parser_profile=parser_profile,
    )
    write_review_files(
        selected_entries_path,
        markdown_path=selected_review_markdown_path,
        csv_path=selected_review_csv_path,
        category=selected_category,
    )
    validate_files(selected_raw_path, entries_path=selected_entries_path, output_path=selected_validation_report_path)

    db_summary: dict[str, Any] | None = None
    if entry_count or allow_empty_db:
        db_summary = build_database(selected_raw_path, selected_entries_path, db_path=selected_db_path)

    return {
        "source_id": selected_source_id,
        "category": selected_category,
        "parser_profile": parser_profile,
        "pdf_path": str(pdf_path),
        "raw_path": str(selected_raw_path),
        "entries_path": str(selected_entries_path),
        "review_markdown_path": str(selected_review_markdown_path),
        "review_csv_path": str(selected_review_csv_path),
        "validation_report_path": str(selected_validation_report_path),
        "db_path": str(selected_db_path) if db_summary else None,
        "entry_count": entry_count,
        "fts_enabled": db_summary["fts_enabled"] if db_summary else None,
        "next_step": None
        if entry_count
        else "No entries were parsed. Inspect the validation report and run OCR or a stronger extraction engine before building the app database.",
    }


def cmd_extract(args: argparse.Namespace) -> None:
    pdf_path = Path(args.pdf)
    category = normalize_category(args.category)
    output_path = Path(args.output) if args.output else default_raw_output(
        pdf_path,
        source_id=args.source_id,
        category=category,
    )
    written_path = extract_to_file(
        pdf_path,
        output_path=output_path,
        source_id=args.source_id,
        category=category,
        source_title=args.source_title,
    )
    print_json({"raw_path": str(written_path), "category": category})


def cmd_parse(args: argparse.Namespace) -> None:
    raw_path = Path(args.raw)
    output_path = Path(args.output) if args.output else None
    written_path, count = parse_raw_file(raw_path, output_path=output_path, parser_profile=args.parser_profile)
    print_json({"entries_path": str(written_path), "entry_count": count, "parser_profile": args.parser_profile})


def cmd_review(args: argparse.Namespace) -> None:
    entries_path = Path(args.entries)
    markdown_path = Path(args.markdown) if args.markdown else default_review_markdown_output(entries_path)
    csv_path = Path(args.csv) if args.csv else default_review_csv_output(entries_path)
    written_markdown_path, written_csv_path, count = write_review_files(entries_path, markdown_path, csv_path)
    print_json(
        {
            "review_markdown_path": str(written_markdown_path),
            "review_csv_path": str(written_csv_path),
            "entry_count": count,
        }
    )


def cmd_validate(args: argparse.Namespace) -> None:
    raw_path = Path(args.raw)
    entries_path = Path(args.entries) if args.entries else None
    output_path = Path(args.output) if args.output else None
    written_path = validate_files(raw_path, entries_path=entries_path, output_path=output_path)
    print_json({"validation_report_path": str(written_path)})


def cmd_build_db(args: argparse.Namespace) -> None:
    raw_path = Path(args.raw)
    entries_path = Path(args.entries)
    db_path = Path(args.db) if args.db else default_db_output()
    summary = build_database(raw_path, entries_path, db_path=db_path)
    print_json(summary)


def cmd_doctor(args: argparse.Namespace) -> None:
    tool_names = ["pdfinfo", "pdftotext", "pdftoppm", "tesseract", "ocrmypdf", "mutool"]
    tools = {tool_name: shutil.which(tool_name) for tool_name in tool_names}
    print_json(
        {
            "python_pdf_engine": "pypdf",
            "parser_profiles": available_parser_profiles(),
            "external_tools": tools,
            "ocr_ready": bool(tools["tesseract"] or tools["ocrmypdf"]),
            "notes": [
                "pypdf is enough for PDFs with embedded text.",
                "Image-only PDFs need OCR before vocabulary parsing can produce entries.",
            ],
        }
    )


def cmd_run_all(args: argparse.Namespace) -> None:
    pdf_path = Path(args.pdf)
    summary = run_pdf_pipeline(
        pdf_path,
        category=normalize_category(args.category),
        source_id=args.source_id,
        source_title=args.source_title,
        parser_profile=args.parser_profile,
        raw_path=Path(args.raw) if args.raw else None,
        entries_path=Path(args.entries) if args.entries else None,
        review_markdown_path=Path(args.review_markdown) if args.review_markdown else None,
        review_csv_path=Path(args.review_csv) if args.review_csv else None,
        validation_report_path=Path(args.report) if args.report else None,
        db_path=Path(args.db) if args.db else None,
        allow_empty_db=args.allow_empty_db,
    )
    print_json(summary)


def cmd_run_batch(args: argparse.Namespace) -> None:
    pdf_paths = discover_pdf_paths(args.inputs)
    summaries = []
    for pdf_path in pdf_paths:
        summaries.append(
            run_pdf_pipeline(
                pdf_path,
                category=category_for_pdf(pdf_path, args),
                parser_profile=args.parser_profile,
                db_path=Path(args.db) if args.db else None,
                allow_empty_db=args.allow_empty_db,
            )
        )
    print_json(
        {
            "pdf_count": len(pdf_paths),
            "entry_count": sum(summary["entry_count"] for summary in summaries),
            "categories": sorted({summary["category"] for summary in summaries}),
            "results": summaries,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract and package vocabulary PDFs for apps.")
    subparsers = parser.add_subparsers(required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract page-level text from a PDF.")
    extract_parser.add_argument("pdf")
    extract_parser.add_argument("--source-id")
    extract_parser.add_argument("--source-title")
    extract_parser.add_argument("--category", default=DEFAULT_CATEGORY)
    extract_parser.add_argument("--output")
    extract_parser.set_defaults(func=cmd_extract)

    parse_parser = subparsers.add_parser("parse", help="Parse raw page text into vocabulary JSONL.")
    parse_parser.add_argument("raw")
    parse_parser.add_argument("--output")
    parse_parser.add_argument("--parser-profile", default=DEFAULT_PARSER_PROFILE, choices=available_parser_profiles())
    parse_parser.set_defaults(func=cmd_parse)

    review_parser = subparsers.add_parser("review", help="Create Markdown and CSV review files.")
    review_parser.add_argument("entries")
    review_parser.add_argument("--markdown")
    review_parser.add_argument("--csv")
    review_parser.set_defaults(func=cmd_review)

    validate_parser = subparsers.add_parser("validate", help="Validate raw and normalized extraction outputs.")
    validate_parser.add_argument("raw")
    validate_parser.add_argument("--entries")
    validate_parser.add_argument("--output")
    validate_parser.set_defaults(func=cmd_validate)

    build_db_parser = subparsers.add_parser("build-db", help="Build or update the SQLite content database.")
    build_db_parser.add_argument("raw")
    build_db_parser.add_argument("entries")
    build_db_parser.add_argument("--db")
    build_db_parser.set_defaults(func=cmd_build_db)

    doctor_parser = subparsers.add_parser("doctor", help="Report available PDF/OCR tooling.")
    doctor_parser.set_defaults(func=cmd_doctor)

    run_all_parser = subparsers.add_parser("run-all", help="Run extract, parse, review, validate, and build-db.")
    run_all_parser.add_argument("pdf")
    run_all_parser.add_argument("--source-id")
    run_all_parser.add_argument("--source-title")
    run_all_parser.add_argument("--category", default=DEFAULT_CATEGORY)
    run_all_parser.add_argument("--parser-profile", default=DEFAULT_PARSER_PROFILE, choices=available_parser_profiles())
    run_all_parser.add_argument("--raw")
    run_all_parser.add_argument("--entries")
    run_all_parser.add_argument("--review-markdown")
    run_all_parser.add_argument("--review-csv")
    run_all_parser.add_argument("--report")
    run_all_parser.add_argument("--db")
    run_all_parser.add_argument("--allow-empty-db", action="store_true")
    run_all_parser.set_defaults(func=cmd_run_all)

    run_batch_parser = subparsers.add_parser("run-batch", help="Run the pipeline for many PDFs or directories.")
    run_batch_parser.add_argument("inputs", nargs="+", help="PDF files or directories to search recursively for PDFs.")
    run_batch_parser.add_argument("--category", help="Use one category for every PDF in this batch.")
    run_batch_parser.add_argument(
        "--category-from-parent",
        action="store_true",
        help="Use each PDF's parent folder name as its category when --category is not set.",
    )
    run_batch_parser.add_argument("--parser-profile", default=DEFAULT_PARSER_PROFILE, choices=available_parser_profiles())
    run_batch_parser.add_argument("--db")
    run_batch_parser.add_argument("--allow-empty-db", action="store_true")
    run_batch_parser.set_defaults(func=cmd_run_batch)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
