#!/bin/bash
# Post-build script to wrap the SPM executable into an .app bundle for iOS simulator
# This is needed because SPM executableTarget doesn't auto-create .app bundles

set -e

BUILD_DIR="${BUILT_PRODUCTS_DIR:-$1}"
EXECUTABLE_NAME="VocabularyApp"
APP_DIR="$BUILD_DIR/${EXECUTABLE_NAME}.app"
EXECUTABLE_PATH="$BUILD_DIR/$EXECUTABLE_NAME"
PLIST_SRC="${SRCROOT:-$2}/Sources/VocabularyApp/AppInfo.plist"
RESOURCES_BUNDLE="$BUILD_DIR/${EXECUTABLE_NAME}_${EXECUTABLE_NAME}.bundle"

if [ ! -f "$EXECUTABLE_PATH" ]; then
    echo "Executable not found at $EXECUTABLE_PATH, skipping app bundle creation."
    exit 0
fi

echo "Creating .app bundle at $APP_DIR"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"

# Copy executable
cp "$EXECUTABLE_PATH" "$APP_DIR/$EXECUTABLE_NAME"

# Copy Info.plist
if [ -f "$PLIST_SRC" ]; then
    cp "$PLIST_SRC" "$APP_DIR/Info.plist"
fi

# Copy resources bundle if it exists
if [ -d "$RESOURCES_BUNDLE" ]; then
    cp -r "$RESOURCES_BUNDLE" "$APP_DIR/"
fi

# Copy any other bundles
for bundle in "$BUILD_DIR"/*.bundle; do
    if [ -d "$bundle" ] && [ "$bundle" != "$RESOURCES_BUNDLE" ]; then
        cp -r "$bundle" "$APP_DIR/"
    fi
done

echo "App bundle created successfully."
ls -la "$APP_DIR"