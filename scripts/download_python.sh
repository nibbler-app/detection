#!/bin/bash
# Download portable Python from python-build-standalone
#
# This script downloads a self-contained Python build that can be bundled
# with the detection engine for maximum portability.
#
# Usage: ./download_python.sh <platform> <output_dir>
# Platforms: macos-arm64, macos-x64, linux-x64, windows-x64

set -e

PLATFORM="${1}"
OUTPUT_DIR="${2:-.}"

if [ -z "$PLATFORM" ]; then
    echo "ERROR: Platform required"
    echo "Usage: $0 <platform> [output_dir]"
    echo "Platforms: macos-arm64, macos-x64, linux-x64, windows-x64"
    exit 1
fi

PYTHON_VERSION="3.12.7"
PYTHON_BUILD_STANDALONE_VERSION="20241016"

# Map platform to python-build-standalone naming
case "$PLATFORM" in
    macos-arm64)
        PBS_PLATFORM="aarch64-apple-darwin"
        PBS_FLAVOR="install_only"
        ARCHIVE_EXT="tar.gz"
        ;;
    macos-x64)
        PBS_PLATFORM="x86_64-apple-darwin"
        PBS_FLAVOR="install_only"
        ARCHIVE_EXT="tar.gz"
        ;;
    linux-x64)
        PBS_PLATFORM="x86_64-unknown-linux-gnu"
        PBS_FLAVOR="install_only"
        ARCHIVE_EXT="tar.gz"
        ;;
    windows-x64)
        PBS_PLATFORM="x86_64-pc-windows-msvc"
        PBS_FLAVOR="install_only"
        ARCHIVE_EXT="tar.gz"
        ;;
    *)
        echo "ERROR: Unknown platform: $PLATFORM"
        exit 1
        ;;
esac

# Construct download URL
FILENAME="cpython-${PYTHON_VERSION}+${PYTHON_BUILD_STANDALONE_VERSION}-${PBS_PLATFORM}-${PBS_FLAVOR}.${ARCHIVE_EXT}"
URL="https://github.com/astral-sh/python-build-standalone/releases/download/${PYTHON_BUILD_STANDALONE_VERSION}/${FILENAME}"

echo "==> Downloading portable Python for $PLATFORM"
echo "    Version: $PYTHON_VERSION"
echo "    URL: $URL"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Download Python
DOWNLOAD_PATH="$OUTPUT_DIR/$FILENAME"
if [ -f "$DOWNLOAD_PATH" ]; then
    echo "==> Python archive already exists: $DOWNLOAD_PATH"
else
    echo "==> Downloading..."
    curl -L -o "$DOWNLOAD_PATH" "$URL"
fi

# Extract Python
EXTRACT_DIR="$OUTPUT_DIR/python"
echo "==> Extracting to: $EXTRACT_DIR"
rm -rf "$EXTRACT_DIR"
mkdir -p "$EXTRACT_DIR"

tar -xzf "$DOWNLOAD_PATH" -C "$EXTRACT_DIR"

# The extracted directory is named 'python'
if [ ! -d "$EXTRACT_DIR/python" ]; then
    echo "ERROR: Expected 'python' directory after extraction"
    exit 1
fi

# Move contents up one level
mv "$EXTRACT_DIR/python"/* "$EXTRACT_DIR/"
rmdir "$EXTRACT_DIR/python"

echo "==> Python downloaded and extracted successfully!"
echo "    Location: $EXTRACT_DIR"
echo "    Size: $(du -sh "$EXTRACT_DIR" | awk '{print $1}')"
