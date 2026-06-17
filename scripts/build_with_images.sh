#!/usr/bin/env bash
#
# End-to-end: generate word images (Azure), rebuild the shared word database from
# every grade, copy the app-data package (db + images + word bundles) into the
# iOS app bundle, and build the app.
#
# Content layout this script assumes:
#   content/<grade>/raw|normalized|lessons|words   <- per-grade source content
#   content/shared/db/vocabulary.sqlite            <- aggregated DB (all grades)
#   content/shared/images/<grade-N_word>.png       <- word images the DB references
#
# Azure credentials are read from the gitignored .env file (no shell exports
# needed). Configure with environment overrides if you like:
#
#   GRADE=4                 Grade to generate images for (default 4)
#   LIMIT=5                 Max words to image this run (default 5; use 0 for ALL)
#   SIMULATOR="iPhone 17"   iOS Simulator device name to build against
#   SKIP_IMAGES=1           Skip image generation (just rebuild DB + bundle + build)
#
# Usage:
#   ./scripts/build_with_images.sh
#   LIMIT=0 ./scripts/build_with_images.sh        # image every word in GRADE
#   SKIP_IMAGES=1 ./scripts/build_with_images.sh  # no image generation
#
set -euo pipefail

# Run from the repository root regardless of where the script is invoked.
cd "$(dirname "$0")/.."

GRADE="${GRADE:-4}"
LIMIT="${LIMIT:-5}"
SIMULATOR="${SIMULATOR:-iPhone 17}"

DB="content/shared/db/vocabulary.sqlite"
WORDS="content/grade-${GRADE}/words/grade-${GRADE}_words.json"
RES="ios/VocabularyApp/Sources/VocabularyApp/Resources"

# Prefer the project virtualenv if present.
PY="./.venv/bin/python"
[[ -x "$PY" ]] || PY="python"

run_cli() { PYTHONPATH=src "$PY" -m vocab_pipeline.cli "$@"; }

# 1. Generate images for the target grade (images land in content/shared/images).
if [[ "${SKIP_IMAGES:-0}" != "1" ]]; then
  echo "==> 1/4 Generating images (grade ${GRADE}, limit ${LIMIT}) via Azure gpt-image-2"
  if [[ -n "${LIMIT}" && "${LIMIT}" != "0" ]]; then
    run_cli generate-images "${WORDS}" --backend azure --write --limit "${LIMIT}"
  else
    run_cli generate-images "${WORDS}" --backend azure --write
  fi
else
  echo "==> 1/4 Skipping image generation (SKIP_IMAGES=1)"
fi

# 2. Rebuild the shared DB from every grade that has a word bundle (aggregates all).
echo "==> 2/4 Rebuilding shared word database from all grades"
shopt -s nullglob
for wf in content/*/words/*_words.json; do
  cat="$(basename "$(dirname "$(dirname "$wf")")")"   # content/grade-4/words/.. -> grade-4
  echo "    + ${cat}: ${wf}"
  run_cli build-word-db "${wf}" --category "${cat}" --db "${DB}"
done
shopt -u nullglob

# 3. Bundle the app-data package into the app's Resources.
echo "==> 3/4 Bundling db + images + word bundles into the app"
mkdir -p "${RES}"
cp "${DB}" "${RES}/vocabulary.sqlite"
cp content/shared/images/*.png "${RES}/" 2>/dev/null || echo "    (no images to copy yet)"
cp content/*/words/*_words.json "${RES}/" 2>/dev/null || true

# 4. Build the iOS app.
echo "==> 4/4 Building the iOS app"
cd ios/VocabularyApp
xcodebuild -scheme VocabularyApp -destination "platform=iOS Simulator,name=${SIMULATOR}" build

echo "==> Done."
