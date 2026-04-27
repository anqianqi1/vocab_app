# Instructions For Future Agents

Read `docs/AGENT_GUIDE.md` before changing this project.

This project is a vocabulary data pipeline. Preserve the layered architecture:

```text
PDF -> raw extraction JSON -> normalized JSONL -> review/validation -> SQLite app database
```

Work under `/home/anqiguo@Apollo.Lab/pjt`. Keep generated data under `data/` and reports under `reports/`. Keep reusable code under `src/vocab_pipeline/` and tests under `tests/`.

Future PDFs may belong to many categories and may use different layouts. Preserve `category`, `source_id`, `source_page`, `source_order`, `raw_entry_text`, `parser_profile`, and `parser_version` through raw JSON, normalized JSONL, review files, validation reports, and SQLite. Add new parser profiles for new layouts instead of weakening the generic parser.

Use `run-all ... --category CATEGORY` for one PDF and `run-batch sources --category-from-parent` for a folder tree such as `sources/classical-roots/*.pdf`.

Important current context: `Vocabulary_from_classical_roots.pdf` opens with `pypdf`, but `pypdf` extracts empty text from all 32 pages. Do not spend time tuning parser heuristics for this PDF until OCR or a stronger extraction backend produces real text.
