from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from .db import build_database, build_word_database, default_db_output, list_words
from .extract import default_raw_output, extract_to_file
from .ids import DEFAULT_CATEGORY, normalize_category, source_id_from_path
from .images import enrich_words_with_images
from .define import rewrite_definitions
from .parse import DEFAULT_PARSER_PROFILE, available_parser_profiles, default_entries_output, parse_raw_file
from .pipeline import PipelineRunner
from .review import default_review_csv_output, default_review_markdown_output, write_review_files
from .structured_extraction import extract_and_write_all_lessons, extract_and_write_words
from .validate import default_report_output, validate_files
from .paths import PipelinePaths


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def discover_source_paths(paths: list[str]) -> list[Path]:
    source_paths: list[Path] = []
    supported_suffixes = {".pdf", ".txt"}
    for raw_path in paths:
        path = Path(raw_path)
        if path.is_dir():
            source_paths.extend(
                sorted(child for child in path.rglob("*") if child.is_file() and child.suffix.lower() in supported_suffixes)
            )
            continue
        if path.is_file() and path.suffix.lower() in supported_suffixes:
            source_paths.append(path)
            continue
        raise FileNotFoundError(f"Expected a PDF or text source file, or a directory containing them: {path}")
    return source_paths


def category_for_source(source_path: Path, args: argparse.Namespace) -> str:
    if getattr(args, "category", None):
        return normalize_category(args.category)
    if getattr(args, "category_from_parent", False):
        return normalize_category(source_path.parent.name)
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
    runner = PipelineRunner()
    result = runner.run_all(
        pdf_path,
        category=category,
        source_id=source_id,
        source_title=source_title,
        parser_profile=parser_profile,
        raw_path=raw_path,
        entries_path=entries_path,
        review_markdown_path=review_markdown_path,
        review_csv_path=review_csv_path,
        validation_report_path=validation_report_path,
        db_path=db_path,
        allow_empty_db=allow_empty_db,
    )
    return result.as_summary()


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


def cmd_build_word_db(args: argparse.Namespace) -> None:
    words_path = Path(args.words)
    db_path = Path(args.db) if args.db else default_db_output()
    summary = build_word_database(words_path, db_path=db_path, category=args.category)
    print_json(summary)


def cmd_list_words(args: argparse.Namespace) -> None:
    db_path = Path(args.db) if args.db else default_db_output()
    words = list_words(args.grade, db_path=db_path)
    if args.limit is not None:
        words = words[: args.limit]
    if args.json:
        print_json({"grade": args.grade, "word_count": len(words), "words": words})
        return
    print(f"Grade {args.grade}: {len(words)} words")
    for word in words:
        image_flag = "\U0001F5BC" if word.get("image") else " "
        print(
            f"  L{word.get('lesson_number'):>2} [{word.get('group'):<9}] "
            f"{image_flag} {word.get('word'):<18} {word.get('root') or '-':<8} "
            f"{(word.get('definition') or '')[:60]}"
        )


def cmd_define_words(args: argparse.Namespace) -> None:
    summary = rewrite_definitions(Path(args.words), deployment=args.deployment, dry_run=not args.write, limit=args.limit)
    print_json(summary)


def cmd_generate_images(args: argparse.Namespace) -> None:
    words_path = Path(args.words)
    summary = enrich_words_with_images(
        words_path,
        images_dir=Path(args.images_dir) if args.images_dir else None,
        backend=args.backend,
        dry_run=not args.write,
        limit=args.limit,
        category=args.category,
        deployment=args.deployment,
    )
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
    source_paths = discover_source_paths(args.inputs)
    runner = PipelineRunner()
    results = runner.run_batch(
        source_paths,
        category=args.category,
        category_from_parent=args.category_from_parent,
        parser_profile=args.parser_profile,
        db_path=Path(args.db) if args.db else None,
        allow_empty_db=args.allow_empty_db,
    )
    summaries = [result.as_summary() for result in results]
    print_json(
        {
            "source_count": len(source_paths),
            "entry_count": sum(summary["entry_count"] for summary in summaries),
            "categories": sorted({summary["category"] for summary in summaries}),
            "results": summaries,
        }
    )


def cmd_extract_lessons(args: argparse.Namespace) -> None:
    source_path = Path(args.source)
    summary = extract_and_write_all_lessons(
        source_path=source_path,
        json_output_path=Path(args.json_output),
        markdown_output_path=Path(args.markdown_output),
    )
    print_json(summary)


def cmd_bundle_lessons(args: argparse.Namespace) -> None:
    raw_path = Path(args.raw)
    paths = PipelinePaths()
    category = paths.category_for_raw(raw_path, category=args.category)
    json_default, markdown_default = paths.lesson_bundle_paths_for_raw(
        raw_path,
        category=category,
        base_name=args.base_name,
    )
    json_output_path = Path(args.json_output) if args.json_output else json_default
    markdown_output_path = Path(args.markdown_output) if args.markdown_output else markdown_default
    summary = extract_and_write_all_lessons(
        source_path=raw_path,
        json_output_path=json_output_path,
        markdown_output_path=markdown_output_path,
    )
    summary["category"] = category
    print_json(summary)


def cmd_bundle_words(args: argparse.Namespace) -> None:
    raw_path = Path(args.raw)
    paths = PipelinePaths()
    category = paths.category_for_raw(raw_path, category=args.category)
    words_default = paths.words_output_path_for_raw(
        raw_path,
        category=category,
    )
    words_output_path = Path(args.words_output) if args.words_output else words_default
    summary = extract_and_write_words(
        source_path=raw_path,
        words_output_path=words_output_path,
        grade=args.grade,
    )
    summary["category"] = category
    print_json(summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract and package vocabulary PDFs for apps.")
    subparsers = parser.add_subparsers(required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract page-level text from a PDF or text source.")
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

    build_word_db_parser = subparsers.add_parser(
        "build-word-db",
        help="Build or update the SQLite word database from a word-centric JSON bundle.",
    )
    build_word_db_parser.add_argument("words")
    build_word_db_parser.add_argument("--db")
    build_word_db_parser.add_argument("--category")
    build_word_db_parser.set_defaults(func=cmd_build_word_db)

    list_words_parser = subparsers.add_parser(
        "list-words",
        help="List all words for a grade from the SQLite word database.",
    )
    list_words_parser.add_argument("--grade", type=int, required=True, help="Grade level (e.g. 4).")
    list_words_parser.add_argument("--db")
    list_words_parser.add_argument("--limit", type=int, help="Show at most this many words.")
    list_words_parser.add_argument("--json", action="store_true", help="Emit full word records as JSON.")
    list_words_parser.set_defaults(func=cmd_list_words)

    generate_images_parser = subparsers.add_parser(
        "generate-images",
        help="Plan or generate one memory-aid image per word and record it in words.json.",
    )
    generate_images_parser.add_argument("words", help="Path to the word-centric words.json bundle.")
    generate_images_parser.add_argument("--images-dir", help="Directory to write image files into.")
    generate_images_parser.add_argument(
        "--backend",
        default="none",
        choices=["none", "openai", "azure"],
        help="Image source backend (default: none, which only plans prompts).",
    )
    generate_images_parser.add_argument(
        "--deployment",
        help="Azure image deployment name (overrides AZURE_OPENAI_IMAGE_DEPLOYMENT).",
    )
    generate_images_parser.add_argument(
        "--write",
        action="store_true",
        help="Actually generate images and update words.json (omit for a no-cost dry run).",
    )
    generate_images_parser.add_argument("--limit", type=int, help="Process at most this many words.")
    generate_images_parser.add_argument("--category")
    generate_images_parser.set_defaults(func=cmd_generate_images)

    define_parser = subparsers.add_parser("define-words", help="Rewrite definitions/examples kid-friendly via Azure chat.")
    define_parser.add_argument("words")
    define_parser.add_argument("--deployment")
    define_parser.add_argument("--limit", type=int)
    define_parser.add_argument("--write", action="store_true")
    define_parser.set_defaults(func=cmd_define_words)

    doctor_parser = subparsers.add_parser("doctor", help="Report available PDF/OCR tooling.")
    doctor_parser.set_defaults(func=cmd_doctor)

    run_all_parser = subparsers.add_parser("run-all", help="Run extract, parse, review, validate, and build-db for a PDF or text source.")
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

    extract_lessons_parser = subparsers.add_parser(
        "extract-lessons",
        help="Extract all lesson content into consolidated JSON and Markdown in lesson-oriented format.",
    )
    extract_lessons_parser.add_argument("source", help="Path to the raw textbook .pages.json source file.")
    extract_lessons_parser.add_argument("--json-output", required=True, help="Path for consolidated lessons JSON output.")
    extract_lessons_parser.add_argument(
        "--markdown-output",
        required=True,
        help="Path for consolidated lessons Markdown output.",
    )
    extract_lessons_parser.set_defaults(func=cmd_extract_lessons)

    bundle_lessons_parser = subparsers.add_parser(
        "bundle-lessons",
        help="Extract lessons into the standard content/<category>/lessons folder.",
    )
    bundle_lessons_parser.add_argument("raw", help="Path to the raw pages JSON file.")
    bundle_lessons_parser.add_argument("--category", help="Optional category override.")
    bundle_lessons_parser.add_argument(
        "--base-name",
        default="all_lessons_extraction",
        help="Filename stem for JSON/Markdown outputs (default: all_lessons_extraction).",
    )
    bundle_lessons_parser.add_argument("--json-output", help="Optional explicit JSON output path.")
    bundle_lessons_parser.add_argument("--markdown-output", help="Optional explicit Markdown output path.")
    bundle_lessons_parser.set_defaults(func=cmd_bundle_lessons)

    bundle_words_parser = subparsers.add_parser(
        "bundle-words",
        help="Produce a word-centric words.json from the raw pages JSON.",
    )
    bundle_words_parser.add_argument("raw", help="Path to the raw pages JSON file.")
    bundle_words_parser.add_argument("--grade", type=int, required=True, help="Grade level (e.g. 4).")
    bundle_words_parser.add_argument("--category", help="Optional category override.")
    bundle_words_parser.add_argument("--words-output", help="Optional explicit words JSON output path.")
    bundle_words_parser.set_defaults(func=cmd_bundle_words)

    return parser


def _load_env_file() -> None:
    """Load variables from a local .env file when python-dotenv is available."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def main() -> None:
    _load_env_file()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
