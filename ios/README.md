# Vocabulary SwiftUI Demo

This folder holds the iOS-first prototype that consumes the pipeline’s packaged SQLite data.

## Structure

```
ios/
  README.md
  VocabularyApp/
    Package.swift
    Sources/
      AppShell/
      VocabularyContent/
      VocabularyData/
      VocabularyFeatures/
      VocabularyApp/
    Tests/
      VocabularyAppTests/
```

- **VocabularyContent** – shared models (`Lesson`, `VocabularyEntry`, `ReviewCard`).
- **VocabularyData** – repositories backed by GRDB, mapping the `sources` and `entries` tables.
- **VocabularyFeatures** – SwiftUI view models and feature reducers.
- **VocabularyApp** – SwiftUI view hierarchy.
- **VocabularyAppTests** – XCTest target for the data layer and feature logic.

## Requirements

- Xcode 15 / iOS 17 SDK.
- Swift Package Manager.
- [GRDB.swift](https://github.com/groue/GRDB.swift) added via SPM.

## Getting Started

1. `mkdir -p ios/VocabularyApp/Sources/VocabularyApp/Resources`
2. `cp content/_shared/db/vocabulary.sqlite ios/VocabularyApp/Sources/VocabularyApp/Resources/vocabulary.sqlite`
3. `cd ios/VocabularyApp` and open the package in Xcode (`xed .`) or run `open Package.swift`.
4. Resolve package dependencies (GRDB is declared in `Package.swift`).
5. Build & run on the iOS 17 simulator; the home screen should load grade‑4 lessons from the bundled DB.

Refer to [docs/app/APP_PLAN.md](../docs/app/APP_PLAN.md) for full context and next steps.

## Troubleshooting

- **Bundle ID crash or blank simulator screen**
  1. Quit Xcode.
  2. Remove `~/Library/Developer/Xcode/DerivedData/VocabularyApp-*`.
  3. Reopen the package (`xed ios/VocabularyApp`).
  4. In Xcode run *Product → Clean Build Folder* (Shift+Command+K).
  5. Run *File → Packages → Reset Package Caches* and wait for resolution.
  6. Rebuild and launch the VocabularyApp scheme.
