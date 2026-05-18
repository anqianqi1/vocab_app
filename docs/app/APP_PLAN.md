# SwiftUI Demo Plan

## 1. Overview
- **Audience**: iOS demo for grade‑4 vocabulary content, showcasing a Duolingo-inspired review loop.
- **Scope**: read-only consumption of pipeline outputs; no authoring or mutation.
- **Outcome**: polished prototype capable of later expansion to Android/web (Flutter or shared Kotlin/JS layer).

## 2. Objectives
1. Deliver a friendly lesson → review → summary flow using a single SwiftUI codebase.
2. Reuse the packaged SQLite database (`content/_shared/db/vocabulary.sqlite`) without modifying pipeline code.
3. Establish clean boundaries and a documented data contract between pipeline and app.

## 3. System Architecture
| Layer | Responsibility |
| --- | --- |
| **AppShell** | `@main` entry, dependency bootstrap, theming, navigation root. |
| **Data Layer** | GRDB wrapper handling SQLite access, migrations, and FTS queries. |
| **Repositories** | `LessonRepository`, `EntryRepository`, `ReviewRepository` returning domain models via async/await. |
| **Use Cases** | Coordinators such as `StartLessonReview`, `RecordQuizResult`, `LoadCompletionSummary`. |
| **Feature Modules** | SwiftUI modules: LessonCatalog, LessonDetail, ReviewSession, CompletionSummary, Settings. |
| **UI** | SwiftUI views with Observation-based view models (unidirectional data flow). |

## 4. Data Contract
Primary artifact: `content/_shared/db/vocabulary.sqlite`

| Table | Purpose | Key Fields |
| --- | --- | --- |
| `sources` | Metadata per textbook | `source_id`, `category`, `source_title`, `page_count`, `extracted_at`, `warnings_json` |
| `entries` | Normalized vocabulary entries | `id`, `term`, `normalized_term`, `definition`, `part_of_speech`, `example`, `section`, `category`, `source_id`, `related_terms_json`, `warnings_json` |
| `entries_fts` | FTS index tied to `entries` | `term`, `definition`, `raw_entry_text` |

Derived models:
- **Lesson**: grouping of entries by `section` + `source_id`.
- **VocabularyEntry**: decoded row with parsed JSON columns (`related_terms`, `warnings`).
- **ReviewCard**: prompt description derived from `VocabularyEntry` (flashcard, multiple choice, fill-in-the-blank).

## 5. User Experience Flow
1. **LessonCatalog** – grid/list of lessons with progress + quick filters.
2. **LessonDetail** – vocabulary list, examples, “Start Practice” CTA.
3. **ReviewSession** – card carousel (flip-to-reveal, multiple choice, fill-in); progress HUD and exit guard.
4. **CompletionSummary** – accuracy stats, suggested next steps, streak-like messaging, share/retake actions.
5. **Settings/About** – data version, pipeline link, debug/test hooks (read-only).

## 6. Build & Bundling Checklist
1. Ensure the resource folder exists: `mkdir -p ios/VocabularyApp/Sources/VocabularyApp/Resources`.
2. Copy the packaged DB: `cp content/_shared/db/vocabulary.sqlite ios/VocabularyApp/Sources/VocabularyApp/Resources/`.
3. Open `ios/VocabularyApp/Package.swift` in Xcode; resolve SPM dependencies (GRDB).
4. Build and run on an iOS 17 simulator; Lesson list should load grade‑4 sections if the resource is bundled correctly.

Bundling steps are mirrored in `ios/README.md` for quick reference.

## 7. Technical Decisions
- Minimum platform: iOS 17 / macOS 14 (Observation, NavigationStack).
- Persistence: [GRDB](https://github.com/groue/GRDB.swift) for performant SQLite + FTS.
- Async/await view models with `@MainActor` guarantees.
- Testing: XCTest + snapshot tests (`swift-snapshot-testing`).
- Project structure: `VocabularyContent`, `VocabularyData`, `VocabularyFeatures`, `VocabularyApp`, `VocabularyAppTests` (Swift Package).

## 8. Separation from Pipeline
- Pipeline owns ETL and generates the SQLite artifact; app consumes it read-only.
- Schema updates require version bump + documented migration steps before app changes land.
- Shared contract documented in this plan and top-level README “App Prototype Status”.
- Future remote sync / analytics endpoints must preserve IDs and column semantics.

## 9. Roadmap / Status
- [x] Add completion summary screen & navigation glue.
