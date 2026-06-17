#!/usr/bin/env bash
#
# Rebuild and SEE the app: sync the latest content (db + images + word bundles)
# into the app bundle, build, assemble a launchable .app (SwiftPM emits only a
# bare executable), then install + launch it in the iOS Simulator.
#
# Usage:
#   ./scripts/run_app.sh
#   SIMULATOR="iPhone 17 Pro" ./scripts/run_app.sh
#
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO/ios/VocabularyApp"

SIMULATOR="${SIMULATOR:-iPhone 17}"
BUNDLE_ID="com.example.vocabularyapp"
DD=".build/dd"
PRODUCTS="$DD/Build/Products/Debug-iphonesimulator"
RES="Sources/VocabularyApp/Resources"

echo "==> 1/5 Syncing latest content into app resources…"
cp "$REPO/content/shared/db/vocabulary.sqlite" "$RES/vocabulary.sqlite" 2>/dev/null || true
cp "$REPO"/content/shared/images/*.png "$RES/" 2>/dev/null || true
cp "$REPO"/content/*/words/*_words.json "$RES/" 2>/dev/null || true
# Strip extended attributes that can break the resource-bundle CodeSign step.
xattr -cr "$RES" 2>/dev/null || true

echo "==> 2/5 Building for ${SIMULATOR}…"
xcodebuild -scheme VocabularyApp \
  -destination "platform=iOS Simulator,name=${SIMULATOR}" \
  -derivedDataPath "$DD" \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO build >/dev/null

echo "==> 3/5 Assembling VocabularyApp.app…"
APP="$PRODUCTS/VocabularyApp.app"
rm -rf "$APP"
mkdir -p "$APP"
cp "$PRODUCTS/VocabularyApp" "$APP/VocabularyApp"
cp Sources/VocabularyApp/AppInfo.plist "$APP/Info.plist"
# SwiftUI @main provides its own scene; drop the templated scene-delegate key.
/usr/libexec/PlistBuddy -c \
  "Delete :UIApplicationSceneManifest:UISceneConfigurations:UIWindowSceneSessionRoleApplication:0:UISceneDelegateClassName" \
  "$APP/Info.plist" 2>/dev/null || true
# Bundle the SwiftPM resource bundles (word data, images, sqlite) next to the binary.
cp -R "$PRODUCTS/VocabularyApp_VocabularyApp.bundle" "$APP/"
[ -d "$PRODUCTS/GRDB_GRDB.bundle" ] && cp -R "$PRODUCTS/GRDB_GRDB.bundle" "$APP/"

echo "==> 4/5 Booting simulator…"
xcrun simctl boot "$SIMULATOR" 2>/dev/null || true
open -a Simulator

echo "==> 5/5 Installing + launching…"
xcrun simctl terminate booted "$BUNDLE_ID" 2>/dev/null || true
xcrun simctl install booted "$APP"
xcrun simctl launch booted "$BUNDLE_ID"

echo "==> Launched. In the app: Grade 4 -> Lesson 1 -> Learn, then tap a card to"
echo "    reveal. Words with images: gradually, graduation, graduate, sensational, sensible."
