# Agent Guide

This guide is for future coding agents and maintainers working on this vocabulary data project.

## Project Goal

The project converts vocabulary PDFs into app-ready data. Treat PDFs as source material, not runtime app data.

The durable flow is:

```text
PDF source files
  -> raw page extraction JSON
  -> normalized vocabulary JSONL
  -> human review artifacts
  -> validation reports
  -> versioned SQLite app content database
```

Apps should consume the SQLite database. JSONL remains the portable build and review format.

## Current Known Source

- `Vocabulary_from_classical_roots.pdf` is the first source PDF.
- `pypdf` can open it and sees 32 pages.
- Initial extraction with `pypdf` returned empty text for all pages, so this PDF likely needs OCR or another extraction engine before real vocabulary entries can be parsed.

## Folder Contract

Keep this structure stable unless there is a strong reason to change it:

```text
pjt/
  sources/       # optional future PDFs, preferably grouped by category
  data/
    raw/          # generated page-level extraction JSON
    normalized/   # generated JSONL vocabulary records
    review/       # generated Markdown/CSV verification artifacts
    db/           # generated SQLite app content database
    exports/      # optional user-facing exports
  docs/           # maintainer and agent documentation
  reports/        # generated validation reports
  src/vocab_pipeline/
  tests/
```

## Commands

Run from `/home/anqiguo@Apollo.Lab/pjt`.

Check available extraction/OCR tooling:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli doctor
```

Run the whole pipeline:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli run-all Vocabulary_from_classical_roots.pdf --category classical-roots
```

Run all PDFs in a source tree, using the parent folder name as the category:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli run-batch sources --category-from-parent
```

Run tests:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m pytest
```

## Maintenance Rules

1. Do not parse PDFs inside an app. Extract and package data ahead of time.
2. Preserve raw extraction artifacts so parser improvements can be audited.
3. Keep normalized records as JSONL: one vocabulary entry per line.
4. Keep `source_id`, `source_page`, `source_order`, and `raw_entry_text` on every parsed entry.
5. Keep `category`, `parser_profile`, and `parser_version` on parsed entries.
6. Add parser profiles for new PDF layouts instead of overfitting the generic parser.
7. Do not overwrite user/app progress when refreshing vocabulary content.
8. Keep mutable app state separate from immutable vocabulary content.
9. Do not build or ship `vocabulary.sqlite` as useful app data until validation shows real entries were parsed.
10. If a PDF extracts as empty text, add OCR or a positional extraction backend before tuning vocabulary parsing.
11. Keep parser heuristics explicit and covered by tests.
12. Do not add large generated files to source control unless the repository owner intentionally wants to version the data package.

## Data Design

Required normalized entry fields:

- `id`
- `term`
- `normalized_term`
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

Optional fields should stay nullable:

- `part_of_speech`
- `root_or_origin`
- `example`
- `section`

Use stable entry IDs derived from source, page, order, and term so repeated imports are idempotent.

Category-aware outputs are partitioned under `data/raw/{category}/`, `data/normalized/{category}/`, `data/review/{category}/`, and `reports/{category}/`. The SQLite database is shared across categories and indexed by `entries.category`.

## Verification Workflow

After extraction:

1. Open the raw JSON and confirm text exists.
2. Open the review Markdown or CSV and read sample entries.
3. Compare samples against the PDF.
4. Check the validation report for missing definitions, duplicates, and empty pages.
5. Only then build or ship the SQLite database.

For this current PDF, expect step 1 to fail with empty text until OCR support is added.

## Future Work

The next likely implementation step is OCR support. Good options:

- Install system tools such as `pdftoppm` and `tesseract`, then add an OCR extraction backend.
- Use `ocrmypdf` to create a text-layer PDF, then rerun the existing `pypdf` extraction.
- Try PyMuPDF or `pdfplumber` if the PDF has embedded text but `pypdf` cannot read it.

When adding a new extraction backend, store the selected backend name in `source.extraction_engine` and keep `pypdf` as the lightweight default for normal text PDFs.
