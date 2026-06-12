# SwiftUI Demo Plan

## 1. Overview
- **Audience**: iOS demo for grade‑4 vocabulary content, showcasing a Duolingo-inspired review loop.
- **Scope**: read-only consumption of pipeline outputs; no authoring or mutation.
- **Outcome**: polished prototype capable of later expansion to Android/web (Flutter or shared Kotlin/JS layer).

## 2. Objectives
1. Deliver a friendly lesson → review → summary flow using a single SwiftUI codebase.
2. Reuse bundled JSON app artifacts (`grade-{N}_all_lessons_extraction.json` and `grade-{N}_words.json`) without parsing raw textbook text in the app.
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
Primary artifacts:

- `content/<grade>/lessons/grade-{N}_all_lessons_extraction.json` — lesson browsing fallback and lesson metadata
- `content/<grade>/lessons/grade-{N}_words.json` — word-centric app data when available

Current app models:

- **StructuredLesson**: lesson metadata, roots, word groups, exercises.
- **WordEntry**: self-contained word unit with grade, lesson, group, root info, definition, example, related words, and exercises.
- **WordDetail**: lightweight per-lesson display model used by existing Learn/Practice screens.

## 5. User Experience Flow
1. **LessonCatalog** – grid/list of lessons with progress + quick filters.
2. **LessonDetail** – vocabulary list, examples, “Start Practice” CTA.
3. **ReviewSession** – card carousel (flip-to-reveal, multiple choice, fill-in); progress HUD and exit guard.
4. **CompletionSummary** – accuracy stats, suggested next steps, streak-like messaging, share/retake actions.
5. **Settings/About** – data version, pipeline link, debug/test hooks (read-only).

## 6. Build & Bundling Checklist
1. Ensure the resource folder exists: `mkdir -p ios/VocabularyApp/Sources/VocabularyApp/Resources`.
2. Copy `grade-{N}_all_lessons_extraction.json` for every supported grade.
3. Copy `grade-{N}_words.json` for grades where word-centric extraction is non-empty.
4. Open `ios/VocabularyApp/Package.swift` in Xcode; resolve SPM dependencies (GRDB).
5. Build and run on an iOS 17 simulator; Lesson list should load bundled grades if resources are present.

Bundling steps are mirrored in `ios/README.md` for quick reference.

## 7. Technical Decisions
- Minimum platform: iOS 17 / macOS 14 (Observation, NavigationStack).
- Persistence: [GRDB](https://github.com/groue/GRDB.swift) for performant SQLite + FTS.
- Async/await view models with `@MainActor` guarantees.
- Testing: XCTest + snapshot tests (`swift-snapshot-testing`).
- Project structure: `VocabularyContent`, `VocabularyData`, `VocabularyFeatures`, `VocabularyApp`, `VocabularyAppTests` (Swift Package).

## 8. Separation from Pipeline
- Pipeline owns ETL and generates bundled JSON artifacts; app consumes them read-only.
- Schema updates require version bump + documented migration steps before app changes land.
- Shared contract documented in this plan and top-level README “App Prototype Status”.
- Future remote sync / analytics endpoints must preserve IDs and column semantics.

## 9. Roadmap / Status

### Completed
- [x] SPM project structure: `VocabularyContent`, `VocabularyData`, `VocabularyFeatures`, `VocabularyApp`, `VocabularyAppTests`
- [x] GRDB integration for SQLite access
- [x] Bundled JSON lesson repository (`BundledLessonRepository`) loading from `grade-{N}_all_lessons_extraction.json`
- [x] Structured domain models: `Grade`, `StructuredLesson`, `WordDetail`, `WordGroup` (key/familiar/challenge)
- [x] `LessonDetailView` with Learn tab and Practice tab (TabView on iPhone, side-by-side on iPad)
- [x] `LearnView` with vocabulary cards grouped by word type
- [x] `ExerciseView` with flashcard, multiple choice, and fill-in-blank review modes
- [x] `ContentView` with adaptive layout:
  - **iPad (width ≥ 640)**: Custom `HStack` split-view with sidebar (grade list → lesson list) and detail area
  - **iPhone (width < 640)**: `NavigationStack` with push navigation (grade picker → lesson list → lesson detail)
- [x] `AppInfo.plist` with `UIDeviceFamily = [1, 2]` for universal iPhone + iPad support
- [x] Xcode scheme with post-action script that creates `.app` bundle (copies executable, Info.plist, and resource bundles)
- [x] `-sectcreate` linker flag embeds Info.plist into binary `__TEXT,__info_plist` section

### In Progress / Known Issues
- [ ] iPad simulator runs app in iPhone compatibility mode despite `UIDeviceFamily = [1, 2]` — worked around via `GeometryReader` width detection
- [ ] `NavigationSplitView` collapses to single column on iPad due to compact size class — replaced with custom `HStack` split-view
- [ ] `UIDevice.current.userInterfaceIdiom` returns `.phone` on iPad simulator — do not use for layout decisions
- [ ] `horizontalSizeClass` returns `.compact` on iPad simulator — do not use for layout decisions

### Next Steps
- [ ] Add grade 5, 8, 10, 11 lesson JSON bundles to Resources
- [ ] Implement review session scoring and progress tracking
- [ ] Add completion summary screen with accuracy stats
- [ ] Add settings/about screen with data version info
- [ ] Investigate root cause of iPad compatibility mode (possibly SPM executable target limitation)
- [ ] Consider migrating to Xcode project (`.xcodeproj`) for proper universal app support
