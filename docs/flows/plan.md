# Grade 4 Extraction Pipeline Plan

_See [docs/README.md](../README.md) for the full documentation map._

## Objective

Extract Grade 4 learning vocabulary from the "Vocabulary From Classical Roots" textbook and build a unified lesson-based data pipeline. Current focus is on extraction and structured source content (not app UI or delivery).

## Implementation Strategy

### 1. Current Focus

- Target Grade 4 textbook extraction from [raw-data/materials/grade-4/808059440-Vocabulary-From-Classical-Roots-Book-4-Grade-4-Student-Book.txt](raw-data/materials/grade-4/808059440-Vocabulary-From-Classical-Roots-Book-4-Grade-4-Student-Book.txt).
- Focus on lesson structure, key vocabulary, related familiar words, example extraction, and exercises.
- Reuse [src/vocab_pipeline](../../src/vocab_pipeline) while retiring artifacts under [archive/legacy_pipeline](../../archive/legacy_pipeline).
- Treat app development as a later phase after extraction is validated.

### 2. Pipeline Architecture

- Source ingestion: `.pdf` and `.txt` textbook exports.
- Raw extraction: page-level JSON with source metadata and page text.
- Normalization: lesson-aware vocabulary entries in JSONL.
- Review: Markdown and CSV review outputs for human verification.
- Validation: JSON reports for data quality and extraction completeness.
- Packaging: SQLite or future lesson JSON exports for app consumption.

### 3. Vocabulary Extraction Pipeline

- Source: the Grade 4 textbook export referenced above.
- Goal: extract lesson sections, key vocabulary, related/familiar terms, definitions, and example sentences.
- Process:
  1. Convert source text into raw page JSON.
  2. Detect lesson headings and assign `section` metadata.
  3. Extract vocabulary entries and related terms.
  4. Capture available example sentences and exercise markers.
  5. Normalize into JSONL records for review and validation.
- Output: structured lesson-based vocabulary entries with source provenance stored under [content/grade-4](../../content/grade-4).
- Use `bundle-lessons` to build per-lesson Markdown/JSON summaries in [content/grade-4/lessons](../../content/grade-4/lessons).

### 4. Review and Validation

- Generate Markdown and CSV review outputs for human verification in [content/grade-4/review](../../content/grade-4/review).
- Produce JSON validation reports in [content/grade-4/reports](../../content/grade-4/reports) for missing definitions, duplicate terms, and extraction coverage.
- Keep review artifacts separate from the SQLite database in [content/shared/db](../../content/shared/db).

### 5. App Packaging (Future Work)

- Package validated lesson vocabulary into SQLite or lesson JSON for future app consumption.
- Preserve source provenance and parser metadata.
- Avoid using raw textbook text as final student-facing content.

### 6. Development Phases

- Phase 1: Stabilize Grade 4 extraction and review.
- Phase 2: Extend the unified pipeline to additional grades and source layouts.
- Phase 3: Build app-facing content generation after the extraction model is validated.

## AI Agent Skills and Workflow Integration

### Skills for AI Agents

1. Textbook Source Extraction
   - Extract text from `.txt` and `.pdf` exports, with Grade 4 `.txt` as the current priority.
   - Preserve metadata fields such as `category`, `source_id`, `source_page`, `source_order`, `section`, `raw_entry_text`, `parser_profile`, and `parser_version`.
   - Add new parser profiles for new layouts instead of weakening the generic parser.

2. Data Pipeline Management
   - Follow the layered architecture:
     - source → raw extraction JSON → normalized JSONL → review/validation → SQLite/app-ready exports
   - Ensure data integrity through all stages of the pipeline.

3. Sentence Generation
   - Use GPT-based models or rule-based templates to generate sentences.
   - Apply filters for originality and child-appropriate content.

4. Content Validation
   - Validate extracted vocabulary and generated sentences for accuracy and appropriateness.
   - Use review files and validation reports to ensure quality.

5. Batch Processing
   - Use `run-all ... --category CATEGORY` for single sources.
   - Use `run-batch sources --category-from-parent` for source directories.

### Workflow for Future Agents

1. Initial Setup
   - Read [docs/agent/AGENT_GUIDE.md](../agent/AGENT_GUIDE.md) for foundational knowledge.
   - Familiarize yourself with the project structure and data pipeline.

2. Handling New Source Layouts
   - For unsupported layout variants, create new parser profiles.
   - Avoid spending time on sources that produce empty text until stronger extraction backends are available.

3. Data Storage
   - Keep generated data under [content](../../content).
   - Store reusable scripts under [src/vocab_pipeline](../../src/vocab_pipeline) and tests under [tests](../../tests).

4. Scalability
   - Design workflows to handle multiple categories and layouts.
   - Ensure the pipeline is modular and extensible for future textbooks.
