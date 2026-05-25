# Vocabulary SwiftUI Demo

This folder holds the iOS-first prototype that consumes the pipeline's packaged lesson JSON data.

## Structure

```
ios/
  README.md
  VocabularyApp/
    Package.swift
    .swiftpm/xcode/xcshareddata/xcschemes/VocabularyApp.xcscheme
    Sources/
      VocabularyApp/         # App entry point, views, Info.plist, Resources
      VocabularyContent/     # Shared domain models (Grade, StructuredLesson, WordDetail)
      VocabularyData/        # Repositories (BundledLessonRepository, SQLiteRepository)
      VocabularyFeatures/    # View models (LearnViewModel, ExerciseViewModel)
    Tests/
      VocabularyAppTests/
```

- **VocabularyContent** - shared models (`Grade`, `StructuredLesson`, `WordDetail`, `WordGroup`, `Lesson`, `VocabularyEntry`, `ReviewCard`).
- **VocabularyData** - repositories backed by GRDB or bundled JSON (`BundledLessonRepository`, `SQLiteRepository`).
- **VocabularyFeatures** - SwiftUI view models (`LearnViewModel`, `ExerciseViewModel`).
- **VocabularyApp** - SwiftUI views (`ContentView`, `LessonDetailView`, `LearnView`, `ExerciseView`), `AppInfo.plist`, and bundled Resources.
- **VocabularyAppTests** - XCTest target for the data layer and feature logic.

## Requirements

- Xcode 16 / iOS 26 SDK (or Xcode 15 / iOS 17 SDK minimum).
- Swift Package Manager (swift-tools-version 5.9).
- [GRDB.swift](https://github.com/groue/GRDB.swift) added via SPM.

## Getting Started

### 1. Bundle lesson data

The app loads lesson data from JSON files in `Sources/VocabularyApp/Resources/`. Copy the pipeline output:

```bash
cp content/grade-4/lessons/all_lessons_extraction.json \
   ios/VocabularyApp/Sources/VocabularyApp/Resources/grade-4_all_lessons_extraction.json
```

Repeat for other grades (grade-5, grade-8, grade-10, grade-11) as they become available.

### 2. Open in Xcode

```bash
cd ios/VocabularyApp
xed .   # or: open Package.swift
```

Resolve package dependencies (GRDB is declared in `Package.swift`).

### 3. Build & Run

Select the **VocabularyApp** scheme and an iOS 17+ simulator.

**Important**: The scheme includes a post-action script that creates the `.app` bundle with `Info.plist` and resource bundles. This is required for the app to launch properly on the simulator.

### 4. Command-line build (alternative)

```bash
cd ios/VocabularyApp

# Build for iPhone simulator
xcodebuild -scheme VocabularyApp \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro' \
  -derivedDataPath /tmp/vocab_build \
  build

# Build for iPad simulator
xcodebuild -scheme VocabularyApp \
  -destination 'platform=iOS Simulator,name=iPad Pro 11-inch (M5)' \
  -derivedDataPath /tmp/vocab_build \
  build
```

After building, the `.app` bundle is at:
`/tmp/vocab_build/Build/Products/Debug-iphonesimulator/VocabularyApp.app`

Install and launch on a booted simulator:
```bash
xcrun simctl install booted /tmp/vocab_build/Build/Products/Debug-iphonesimulator/VocabularyApp.app
xcrun simctl launch booted com.example.vocabularyapp
```

## Architecture Notes

### Adaptive Layout

The app uses `GeometryReader` to detect screen width and branch between iPad and iPhone layouts:

- **iPad (width >= 640pt)**: Custom `HStack` split-view with sidebar (grade list -> lesson list) and detail area. `LessonDetailView` shows Learn and Practice side-by-side.
- **iPhone (width < 640pt)**: `NavigationStack` with push navigation. `LessonDetailView` uses `TabView` for Learn/Practice tabs.

**Do NOT use `UIDevice.current.userInterfaceIdiom` or `@Environment(\.horizontalSizeClass)`** for layout decisions - they return `.phone`/`.compact` on iPad simulator due to a known compatibility mode issue with SPM executable targets.

### Info.plist

`AppInfo.plist` declares `UIDeviceFamily = [1, 2]` (iPhone + iPad). It is:
1. Embedded into the binary via `-sectcreate __TEXT __info_plist` linker flag
2. Copied to the `.app` bundle by the scheme's post-action script

### Data Flow

```
Pipeline output (JSON) -> BundledLessonRepository -> ContentView -> LessonDetailView
                                                                    |-- LearnView (LearnViewModel)
                                                                    +-- ExerciseView (ExerciseViewModel)
```

## Troubleshooting

- **"Supported platforms for the buildables in the current scheme is empty"**: This is a known warning from SPM executable targets. The build still succeeds.
- **App shows iPhone layout on iPad simulator**: Known issue. The `GeometryReader` workaround ensures the iPad layout is used when screen width >= 640pt.
- **Bundle ID crash or blank simulator screen**:
  1. Quit Xcode.
  2. Remove `~/Library/Developer/Xcode/DerivedData/VocabularyApp-*`.
  3. Reopen the package (`xed ios/VocabularyApp`).
  4. In Xcode run *Product -> Clean Build Folder* (Shift+Command+K).
  5. Run *File -> Packages -> Reset Package Caches* and wait for resolution.
  6. Rebuild and launch the VocabularyApp scheme.
- **"Executable not found" in post-action script**: The scheme's post-action script runs after each build. If you see this message, the build may have failed. Check the build output for errors.
