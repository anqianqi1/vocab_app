# Vocabulary Data Pipeline

Structured content extractor for the *Vocabulary From Classical Roots* series. The current scope covers data ingestion and packaging; Duolingo-style app logic (APIs, UI, spaced repetition) comes later.

---

## At a Glance

- ✅ **Pipeline**: Grade 4, 5, 8, 10, and 11 `.txt` sources run end-to-end (raw JSON -> JSONL -> review -> validation -> SQLite).
- ✅ **Lesson bundles**: Markdown + JSON summaries for every processed grade (`content/<grade>/lessons/`).
- ✅ **iOS App**: SwiftUI prototype with adaptive iPhone/iPad layout, lesson browsing, and review exercises. See [ios/README.md](ios/README.md).
- 🟡 **Next phase**: design learner app + backend while keeping data pipeline stable.

---

## Documentation Map

| Reference | Description |
| --- | --- |
| [docs/README.md](docs/README.md) | Documentation hub and table of contents |
| [docs/agent/AGENT_GUIDE.md](docs/agent/AGENT_GUIDE.md) | Operational playbook for coding agents |
| [docs/flows/plan.md](docs/flows/plan.md) | Grade-level extraction roadmap and milestones |
| [ai_agent_flows/](ai_agent_flows/README.md) | Session logs and runbooks (create/update per engagement) |

Every time you touch the project, add a dated note under `ai_agent_flows/` and update the “Recent Updates” list in `docs/README.md`.

---

## Repository Map

| Path | Purpose |
| --- | --- |
| [sources/materials](sources/materials) | Raw textbooks (`.txt`, archival PDFs) grouped by category |
| [content/](content) | Per-category outputs: `raw`, `normalized`, `review`, `reports`, `lessons` |
| [content/_shared/db](content/_shared/db) | App-ready SQLite (`vocabulary.sqlite`) |
| [src/vocab_pipeline](src/vocab_pipeline) | Extraction, parsing, validation code |
| [tests/](tests) | Pytest suite (parsing + path helpers) |
| [docs/](docs) | Maintainer & agent documentation |
| [ai_agent_flows/](ai_agent_flows) | Templates / scratchpad for agent workflows |
| [data/exports/](data/exports) | Optional manual exports (currently empty) |
| [archive/legacy_pipeline/](archive/legacy_pipeline) | Legacy layout note (kept for history only) |

---

## Workflow Overview

1. **Extract** – `extract`/`run-all` produces `content/<category>/raw/*.pages.json`.
2. **Parse** – raw pages → vocabulary entries (`normalized/*.entries.jsonl`).
3. **Review** – Markdown + CSV decks for human QA (`review/`).
4. **Validate** – data quality metrics (`reports/`).
5. **Bundle** – lesson summaries (`lessons/all_lessons_extraction.{json,md}`).
6. **Package** – refresh shared SQLite (`content/_shared/db/vocabulary.sqlite`).

---

## Environment Setup

```bash
git clone <repo-url>
cd vocab_app

# create & activate virtual environment (macOS/Linux)
python3 -m venv .venv
source .venv/bin/activate

# install dependencies
pip install --upgrade pip
pip install -e .[dev]

# verify installation
PYTHONPATH=src python -m pytest
```

On Windows powershell: `python -m venv .venv; .\.venv\Scripts\Activate.ps1`.

---

## Core Commands

### Diagnostics
```bash
PYTHONPATH=src python -m vocab_pipeline.cli doctor
```

### One-shot pipeline
```bash
PYTHONPATH=src python -m vocab_pipeline.cli run-all sources/materials/808059440-Vocabulary-From-Classical-Roots-Book-4-Grade-4-Student-Book.txt --category grade-4
```

### Batch processing
```bash
PYTHONPATH=src python -m vocab_pipeline.cli run-batch sources --category-from-parent
```

### Stage-by-stage
```bash
PYTHONPATH=src python -m vocab_pipeline.cli extract  sources/materials/Vocabulary_from_classical_roots.pdf --category classical-roots
PYTHONPATH=src python -m vocab_pipeline.cli parse    content/classical-roots/raw/classical-roots-vocabulary-from-classical-roots.pages.json
PYTHONPATH=src python -m vocab_pipeline.cli review   content/classical-roots/normalized/classical-roots-vocabulary-from-classical-roots.entries.jsonl
PYTHONPATH=src python -m vocab_pipeline.cli validate content/classical-roots/raw/classical-roots-vocabulary-from-classical-roots.pages.json --entries content/classical-roots/normalized/classical-roots-vocabulary-from-classical-roots.entries.jsonl
PYTHONPATH=src python -m vocab_pipeline.cli build-db content/classical-roots/raw/classical-roots-vocabulary-from-classical-roots.pages.json content/classical-roots/normalized/classical-roots-vocabulary-from-classical-roots.entries.jsonl
```

### Lesson bundles (default destinations)
```bash
PYTHONPATH=src python -m vocab_pipeline.cli bundle-lessons content/grade-4/raw/grade-4-808059440-vocabulary-from-classical-roots-book-4-grade-4-student-book.pages.json
```

### Process every grade at once
```bash
PYTHONPATH=src python -m vocab_pipeline.cli run-batch sources --category-from-parent --allow-empty-db
```

The default parser profile is `generic`. Create new profiles for different layouts instead of modifying the generic rules.

---

## App Prototype Status

- SwiftUI demo targeting grade-4 content is defined in [docs/app/APP_PLAN.md](docs/app/APP_PLAN.md).
- The app consumes `content/_shared/db/vocabulary.sqlite` read-only; the pipeline remains the authoritative producer.
- Any schema changes must be coordinated—update both the pipeline migration docs and the SwiftUI plan before shipping.

---

## Data Products

- **Raw pages** – `content/<grade>/raw/*.pages.json`
- **Normalized entries** – `content/<grade>/normalized/*.entries.jsonl`
- **Review decks** – `content/<grade>/review/*.review.{md,csv}`
- **Validation reports** – `content/<grade>/reports/*.validation.json`
- **Lesson bundles** – `content/<grade>/lessons/all_lessons_extraction.{json,md}`
- **App database** – `content/_shared/db/vocabulary.sqlite`

All current grades (4, 5, 8, 10, 11) produce 147–203 entries across 16 lessons each.

| Stage | Files | Location |
| --- | --- | --- |
| Extract | `*.pages.json` | `content/<grade>/raw/` |
| Parse | `*.entries.jsonl` | `content/<grade>/normalized/` |
| Review | `*.review.{md,csv}` | `content/<grade>/review/` |
| Validate | `*.validation.json` | `content/<grade>/reports/` |
| Bundle | `all_lessons_extraction.{json,md}` | `content/<grade>/lessons/` |
| Package | `vocabulary.sqlite` | `content/_shared/db/` |

---

## Quality & Testing

- Unit tests: `/Users/anqiguo/Documents/Projects/vocab_app/.venv/bin/python -m pytest`
- Validation check: inspect `content/<grade>/reports/*.validation.json` (status `ok` expected)
- Manual QA: review Markdown decks before shipping updated datasets

---

## Roadmap

1. **Data foundation** *(complete)* – multi-grade extraction pipeline.
2. **Extensibility** – parser profiles for other layouts, OCR support for image-only PDFs.
3. **App layer** *(upcoming)* – learner UX, scheduling, progress storage, API design.
4. **Scale-out** – additional textbooks/grades plugged into the same pipeline.

---

## Documentation & Agent Guides

- [docs/README.md](docs/README.md) – documentation index & update conventions
- [docs/agent/AGENT_GUIDE.md](docs/agent/AGENT_GUIDE.md) – operational playbook for coding agents
- [docs/flows/plan.md](docs/flows/plan.md) – grade-level extraction roadmap
- [ai_agent_flows/README.md](ai_agent_flows/README.md) – record agent-specific workflows or session notes

Keep these references current so future maintainers (human or AI) can understand the project at a glance.
