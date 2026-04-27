# Vocabulary Data Pipeline

This project turns vocabulary PDFs into a reusable data package for apps.

The pipeline keeps three layers separate:

1. **Raw extraction**: page-level text and PDF metadata for auditability.
2. **Normalized records**: one vocabulary entry per JSONL line for review and interchange.
3. **App database**: a SQLite content database that can be bundled with Windows, macOS, iOS, desktop, or web apps.

The PDF is source material. Apps should consume the generated SQLite database, not the PDF directly.

## Layout

```text
pjt/
  Vocabulary_from_classical_roots.pdf
  sources/       # optional future input PDFs grouped by category
  data/
    raw/          # page-level extraction artifacts
    normalized/   # JSONL vocabulary records
    review/       # Markdown/CSV files for human verification
    db/           # SQLite app content database
    exports/      # optional exports for spreadsheet/manual workflows
  reports/        # validation reports
  src/vocab_pipeline/
  tests/
```

## Quick Start

From this folder:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli run-all Vocabulary_from_classical_roots.pdf --category classical-roots
```

This writes:

- `data/raw/classical-roots/classical-roots-vocabulary-from-classical-roots.pages.json`
- `data/normalized/classical-roots/classical-roots-vocabulary-from-classical-roots.entries.jsonl`
- `data/review/classical-roots/classical-roots-vocabulary-from-classical-roots.review.md`
- `data/review/classical-roots/classical-roots-vocabulary-from-classical-roots.review.csv`
- `reports/classical-roots/classical-roots-vocabulary-from-classical-roots.validation.json`
- `data/db/vocabulary.sqlite` when parsed entries exist

If a PDF has no extractable text, the raw artifact and validation report will say so. In that case the next step is OCR or a different extraction engine; the app database should only be built from reviewed vocabulary records.

## Commands

Check available PDF/OCR tooling:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli doctor
```

Run the full local pipeline:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli run-all Vocabulary_from_classical_roots.pdf --category classical-roots
```

Run many future PDFs. A practical layout is one folder per category:

```text
sources/
  classical-roots/
    Vocabulary_from_classical_roots.pdf
  medical/
    medical_terms.pdf
  sat/
    sat_word_list.pdf
```

Then process everything with the parent folder as the category:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli run-batch sources --category-from-parent
```

If every PDF in a batch belongs to one category, pass it directly:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli run-batch sources/classical-roots --category classical-roots
```

Run stages separately:

```bash
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli extract Vocabulary_from_classical_roots.pdf --category classical-roots
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli parse data/raw/classical-roots/classical-roots-vocabulary-from-classical-roots.pages.json
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli review data/normalized/classical-roots/classical-roots-vocabulary-from-classical-roots.entries.jsonl
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli validate data/raw/classical-roots/classical-roots-vocabulary-from-classical-roots.pages.json --entries data/normalized/classical-roots/classical-roots-vocabulary-from-classical-roots.entries.jsonl
PYTHONPATH=src /usr/local/bin/python3.12 -m vocab_pipeline.cli build-db data/raw/classical-roots/classical-roots-vocabulary-from-classical-roots.pages.json data/normalized/classical-roots/classical-roots-vocabulary-from-classical-roots.entries.jsonl
```

The current parser profile is `generic`. Future PDFs with different layouts should get new parser profiles instead of changing the generic parser for every source.

## Data Model

Each normalized vocabulary entry contains source-tracking fields:

- `id`
- `term`
- `normalized_term`
- `definition`
- `part_of_speech`
- `root_or_origin`
- `example`
- `section`
- `category`
- `source_id`
- `source_page`
- `source_order`
- `raw_entry_text`
- `parser_profile`
- `parser_version`
- `review_status`
- `warnings`

Keep app/user state separate from this source content. Favorites, notes, learning progress, quiz history, and spaced-repetition state should live in a separate user database or separate mutable tables.

## App Packaging

Use `data/db/vocabulary.sqlite` as the read-only content package for apps.

- Windows/macOS desktop: bundle the SQLite file with Electron, Tauri, Qt, .NET MAUI, or native apps.
- iOS: bundle the same SQLite file as an app resource and query it locally.
- Web/backend: query SQLite from the backend, or migrate the same schema to PostgreSQL later if remote multi-user sync is needed.

## Verification

Always inspect the generated review file before using the data in an app. It includes parsed fields, source pages, raw entry text, and parser warnings.

For future maintainers and coding agents, see `docs/AGENT_GUIDE.md`.
