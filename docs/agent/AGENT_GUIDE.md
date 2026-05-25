# Agent Guide

_For the full documentation index see [docs/README.md](../README.md)._ 

This guide is for future coding agents and maintainers working on the vocabulary extraction pipeline.

## Project Goal

The project converts textbook source material into lesson-based vocabulary data for future learning apps. The current focus is on extracting Grade 4 textbook content from the "Vocabulary From Classical Roots" series.

The durable flow is:

```text
PDF and raw text source files
  -> raw page extraction JSON
  -> normalized vocabulary JSONL
  -> human review artifacts
  -> validation reports
  -> versioned SQLite app content database
```

Apps should consume the SQLite database or a structured lesson content export. JSONL remains the portable normalized and review format.

## Current Focus

- Current source: [sources/materials/808059440-Vocabulary-From-Classical-Roots-Book-4-Grade-4-Student-Book.txt](sources/materials/808059440-Vocabulary-From-Classical-Roots-Book-4-Grade-4-Student-Book.txt)
- The pipeline now targets Grade 4 textbook extraction as the starting point for the unified workflow.
- Prior work under [archive/legacy_pipeline](archive/legacy_pipeline) is no longer the active extraction path and should not be used for new builds.
- The extraction workflow now supports raw `.txt` textbook exports as a first-class source format.

## Folder Contract

- [sources/](sources) — grouped raw inputs (.txt, .pdf)
- [content/](content) — per-category folders containing `raw`, `normalized`, `review`, `reports`, and `lessons`
- [content/_shared/db](content/_shared/db) — shared SQLite database for apps
- [archive/legacy_pipeline](archive/legacy_pipeline) — frozen artifacts from the previous layout
- [data/exports](data/exports) — optional manual exports
- [docs/](docs) — maintainer and agent documentation
- [src/vocab_pipeline/](src/vocab_pipeline) — extraction and packaging code
- [tests/](tests) — automated test suite

## Commands

Run from the project root.

Check available extraction/OCR tooling:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli doctor
```

Run the whole pipeline for a PDF or a raw text textbook export:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli run-all sources/materials/808059440-Vocabulary-From-Classical-Roots-Book-4-Grade-4-Student-Book.txt --category grade-4
```

Generate consolidated lesson bundles (JSON + Markdown) for an extracted raw payload:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli bundle-lessons content/grade-4/raw/grade-4-808059440-vocabulary-from-classical-roots-book-4-grade-4-student-book.pages.json
```

Run all source files in a directory tree, using the parent folder name as the category:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli run-batch sources --category-from-parent
```

Run tests:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m pytest
```

## Maintenance Rules

1. Do not parse textbook source files inside an app. Extract and package data ahead of time.
2. Preserve raw extraction artifacts so parser improvements can be audited.
3. Keep normalized records as JSONL: one vocabulary entry per line.
4. Keep `source_id`, `source_page`, `source_order`, and `raw_entry_text` on every parsed entry.
5. Keep `category`, `parser_profile`, and `parser_version` on parsed entries.
6. Use lesson `section` metadata to preserve the textbook lesson unit for each entry.
7. Capture `related_terms` from root/familiar word groups when available.
8. Capture extracted example sentences if they appear in the source text.
9. Add parser profiles for new textbook layouts instead of overfitting the generic parser.
10. Do not overwrite user/app progress when refreshing vocabulary content.
11. Keep mutable app state separate from immutable vocabulary content.
12. Do not build or ship the SQLite database until validation shows real entries were parsed.
13. If a source extracts as empty text, add OCR or a positional extraction backend before tuning vocabulary parsing.
14. Keep parser heuristics explicit and covered by tests.
15. Do not add large generated files to source control unless the repository owner intentionally wants to version the data package.
16. Ensure extracted entries align with lesson structure and include accurate definitions, word types, and example sentences.

## Data Design

Required normalized entry fields:

- `id`
- `term`
- `normalized_term`
- `word_type`
- `definition`
- `category`
- `source_id`
- `source_page`
- `source_order`
- `raw_entry_text`
- `parser_profile`
- `parser_version`
- `review_status`
- `warnings`
- `related_terms`

Optional fields should stay nullable:

- `part_of_speech`
- `root_or_origin`
- `example`
- `section`

Use stable entry IDs derived from source, page, order, and term so repeated imports are idempotent.

Category-aware outputs live under [content](content): each grade folder contains `raw`, `normalized`, `review`, `reports`, and `lessons`. The shared SQLite database sits in [content/_shared/db/vocabulary.sqlite](content/_shared/db/vocabulary.sqlite) and is indexed by `entries.category`.

## Verification Workflow

After extraction:

1. Open the raw JSON and confirm text exists.
2. Open the review Markdown or CSV and read sample entries.
3. Compare samples against the PDF.
4. Check the validation report for missing definitions, duplicates, and empty pages.
5. Only then build or ship the SQLite database.

For image-only PDFs, expect step 1 to fail until OCR support is added.

## Future Work

The next likely implementation step is OCR support. Good options:

- Install system tools such as `pdftoppm` and `tesseract`, then add an OCR extraction backend.
- Use `ocrmypdf` to create a text-layer PDF, then rerun the existing `pypdf` extraction.
- Try PyMuPDF or `pdfplumber` if the PDF has embedded text but `pypdf` cannot read it.

When adding a new extraction backend, store the selected backend name in `source.extraction_engine` and keep `pypdf` as the lightweight default for normal text PDFs.

## iOS App

The project includes an iOS SwiftUI prototype under `ios/VocabularyApp/`. See [ios/README.md](../../ios/README.md) and [docs/app/APP_PLAN.md](../app/APP_PLAN.md) for full details.

### Key facts for agents

- **SPM executable target**: The app is built as a Swift Package Manager executable, not a traditional `.xcodeproj`. This has implications for platform detection.
- **Adaptive layout**: Uses `GeometryReader` width detection (>= 640pt = iPad, < 640pt = iPhone). Do NOT use `UIDevice.current.userInterfaceIdiom` or `horizontalSizeClass` - they return iPhone values on iPad simulator.
- **Info.plist**: Declares `UIDeviceFamily = [1, 2]` for universal support. Embedded via `-sectcreate __TEXT __info_plist` linker flag AND copied to `.app` bundle by scheme post-action script.
- **Scheme post-action**: The `.xcscheme` file contains a shell script that creates the `.app` bundle after each build. If the scheme file is missing, the app won't launch on simulator.
- **Data source**: Currently loads from bundled JSON files (`grade-{N}_all_lessons_extraction.json`), not SQLite. The `BundledLessonRepository` reads these from `Sources/VocabularyApp/Resources/`.
- **Module structure**: `VocabularyContent` (models) -> `VocabularyData` (repositories) -> `VocabularyFeatures` (view models) -> `VocabularyApp` (views + entry point)

### Build commands

```bash
cd ios/VocabularyApp

# Build for simulator
xcodebuild -scheme VocabularyApp \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  -derivedDataPath /tmp/vocab_build \
  build

# Install and launch on booted simulator
xcrun simctl install booted /tmp/vocab_build/Build/Products/Debug-iphonesimulator/VocabularyApp.app
xcrun simctl launch booted com.example.vocabularyapp
```
