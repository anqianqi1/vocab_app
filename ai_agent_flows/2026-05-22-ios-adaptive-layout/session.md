# iOS Adaptive Layout - Session Log

**Date**: 2026-05-22
**Goal**: Fix iPad simulator showing iPhone layout instead of proper iPad split-view.

## Summary

The iOS app was showing the iPhone `NavigationStack` layout on iPad simulator. After extensive debugging, the root cause was identified: the SPM executable target runs in iPhone compatibility mode on iPad, causing `UIDevice.current.userInterfaceIdiom` to return `.phone` and `horizontalSizeClass` to return `.compact` even on iPad Pro simulators.

## Root Cause

- `UIDeviceFamily = [1, 2]` is correctly declared in `AppInfo.plist`
- The plist is embedded via `-sectcreate __TEXT __info_plist` AND copied to `.app/Info.plist`
- Despite this, the system treats the app as iPhone-only on iPad
- This is likely a limitation of SPM executable targets (not traditional `.xcodeproj`)

## Solution

Replaced idiom/SizeClass-based layout detection with `GeometryReader`-based width detection:

- **iPad (width >= 640pt)**: Custom `HStack` split-view with sidebar + detail
- **iPhone (width < 640pt)**: `NavigationStack` with push navigation

## Files Changed

| File | Change |
|------|--------|
| `ios/VocabularyApp/Sources/VocabularyApp/ContentView.swift` | Complete rewrite: `GeometryReader` branching, custom `HStack` iPad layout, `NavigationStack` iPhone layout |
| `ios/VocabularyApp/Package.swift` | Removed `-sectcreate` linker settings (post-action script handles Info.plist) |
| `ios/VocabularyApp/.swiftpm/xcode/xcshareddata/xcschemes/VocabularyApp.xcscheme` | Recreated scheme file with post-action `.app` bundle creation script |
| `ios/README.md` | Updated with current structure, build commands, architecture notes, troubleshooting |
| `docs/app/APP_PLAN.md` | Updated roadmap with completed items, known issues, next steps |
| `docs/agent/AGENT_GUIDE.md` | Added iOS app section with key facts and build commands |
| `docs/README.md` | Updated recent updates and table of contents |
| `README.md` | Added iOS app status to "At a Glance" |

## Known Issues

1. **iPad compatibility mode**: App runs in iPhone compatibility mode on iPad. Worked around via `GeometryReader`. Root cause (SPM limitation) not yet fixed.
2. **"Supported platforms empty" warning**: Harmless xcodebuild warning from SPM executable targets.
3. **Scheme file fragility**: The `.xcscheme` file can be deleted by Xcode. Must be recreated if missing.

## Build & Test Commands

```bash
cd ios/VocabularyApp

# Build
xcodebuild -scheme VocabularyApp \
  -destination 'platform=iOS Simulator,name=iPad Pro 11-inch (M5)' \
  -derivedDataPath /tmp/vocab_build \
  build

# Create .app bundle (post-action script does this automatically in Xcode)
APP_DIR=/tmp/vocab_build/Build/Products/Debug-iphonesimulator/VocabularyApp.app
mkdir -p "$APP_DIR"
cp /tmp/vocab_build/Build/Products/Debug-iphonesimulator/VocabularyApp "$APP_DIR/"
cp ios/VocabularyApp/Sources/VocabularyApp/AppInfo.plist "$APP_DIR/Info.plist"
for bundle in /tmp/vocab_build/Build/Products/Debug-iphonesimulator/*.bundle; do
  [ -d "$bundle" ] && cp -r "$bundle" "$APP_DIR/"
done

# Install & launch
xcrun simctl install booted "$APP_DIR"
xcrun simctl launch booted com.example.vocabularyapp

# Screenshot
xcrun simctl io booted screenshot /tmp/ipad_test.png
```

## Lessons Learned

1. **Never use `UIDevice.current.userInterfaceIdiom` for layout** in SPM executable targets — it lies on iPad.
2. **Never use `@Environment(\.horizontalSizeClass)` for layout** — same reason.
3. **`GeometryReader` at the root of `body`** is the most reliable way to detect actual screen width.
4. **`NavigationSplitView` collapses** when size class is compact — useless on iPad in compatibility mode.
5. **The `.xcscheme` post-action script** is critical — without it, there's no `.app` bundle and the app won't launch.
6. **Always test on both iPhone and iPad simulators** after layout changes.