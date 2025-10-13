#!/bin/bash
# Optimized Bundle Python engine for distribution
#
# This script packages the Python detection code and virtual environment
# into a distributable tar.gz bundle with aggressive size optimization.
#
# Usage: ./bundle_python_engine_optimized.sh [output_dir]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${1:-$PROJECT_ROOT/dist}"
ENGINE_ID="hand_near_face"

# Read version from VERSION file
VERSION_FILE="$PROJECT_ROOT/VERSION"
if [ ! -f "$VERSION_FILE" ]; then
    echo "ERROR: VERSION file not found at $VERSION_FILE"
    exit 1
fi
VERSION=$(cat "$VERSION_FILE")

echo "==> Bundling Python engine (OPTIMIZED): $ENGINE_ID v$VERSION"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Create temporary build directory
TEMP_DIR=$(mktemp -d)
BUILD_DIR="$TEMP_DIR/$ENGINE_ID"
mkdir -p "$BUILD_DIR"

echo "==> Using temporary directory: $TEMP_DIR"

# Copy detection code
echo "==> Copying detection code..."
if [ -d "$PROJECT_ROOT/src" ]; then
    cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/src"
else
    cp -r "$PROJECT_ROOT/python_app" "$BUILD_DIR/src"
fi

# Remove unnecessary files from detection code
rm -rf "$BUILD_DIR/src/__pycache__"
rm -rf "$BUILD_DIR/src/.pytest_cache"
rm -f "$BUILD_DIR/src"/*.pyc

# Copy virtual environment
echo "==> Copying Python virtual environment..."
if [ -d "$PROJECT_ROOT/venv" ]; then
    cp -r "$PROJECT_ROOT/venv" "$BUILD_DIR/python"

    echo "==> Optimizing bundle size..."
    SITE_PACKAGES="$BUILD_DIR/python/lib/python*/site-packages"

    # 1. Remove pip and setuptools
    echo "  - Removing pip and setuptools..."
    rm -rf $SITE_PACKAGES/pip
    rm -rf $SITE_PACKAGES/setuptools
    rm -rf $SITE_PACKAGES/wheel
    rm -rf $SITE_PACKAGES/pkg_resources

    # 2. Remove all .pyc files and __pycache__
    echo "  - Removing .pyc files and __pycache__..."
    find "$BUILD_DIR/python" -name "*.pyc" -delete
    find "$BUILD_DIR/python" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

    # 3. Remove test directories and files
    echo "  - Removing test files..."
    find $SITE_PACKAGES -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
    find $SITE_PACKAGES -type d -name "test" -exec rm -rf {} + 2>/dev/null || true
    find $SITE_PACKAGES -type d -name "testing" -exec rm -rf {} + 2>/dev/null || true
    find $SITE_PACKAGES -name "*test*.py" -not -path "*/site-packages/mediapipe/*" -delete 2>/dev/null || true

    # 4. Remove examples and documentation
    echo "  - Removing examples and docs..."
    find $SITE_PACKAGES -type d -name "examples" -exec rm -rf {} + 2>/dev/null || true
    find $SITE_PACKAGES -type d -name "example" -exec rm -rf {} + 2>/dev/null || true
    find $SITE_PACKAGES -type d -name "docs" -exec rm -rf {} + 2>/dev/null || true
    find $SITE_PACKAGES -type d -name "doc" -exec rm -rf {} + 2>/dev/null || true
    find $SITE_PACKAGES -name "*.md" -delete 2>/dev/null || true
    find $SITE_PACKAGES -name "*.rst" -delete 2>/dev/null || true
    find $SITE_PACKAGES -name "*.txt" -not -name "top_level.txt" -delete 2>/dev/null || true

    # 5. Remove locale files (keep only English if needed)
    echo "  - Removing locale files..."
    find $SITE_PACKAGES -type d -name "locale" -exec rm -rf {} + 2>/dev/null || true
    find $SITE_PACKAGES -type d -name "locales" -exec rm -rf {} + 2>/dev/null || true

    # 6. Remove unnecessary matplotlib backends and data
    echo "  - Optimizing matplotlib..."
    rm -rf $SITE_PACKAGES/matplotlib/mpl-data/sample_data 2>/dev/null || true
    rm -rf $SITE_PACKAGES/matplotlib/tests 2>/dev/null || true

    # 7. Remove JAX examples and tests (JAX is huge)
    echo "  - Optimizing JAX/JAXlib..."
    rm -rf $SITE_PACKAGES/jax/tests 2>/dev/null || true
    rm -rf $SITE_PACKAGES/jax/experimental/jax2tf/tests 2>/dev/null || true
    rm -rf $SITE_PACKAGES/jaxlib/examples 2>/dev/null || true

    # 8. Remove OpenCV data files we don't need
    echo "  - Optimizing OpenCV..."
    rm -rf $SITE_PACKAGES/cv2/data 2>/dev/null || true

    # 9. Remove SciPy test data
    echo "  - Optimizing SciPy..."
    find $SITE_PACKAGES/scipy -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true

    # 10. Strip debug symbols from native libraries (can save 30-50%)
    if command -v strip &> /dev/null; then
        echo "  - Stripping debug symbols from native libraries..."
        find "$BUILD_DIR/python" \( -name "*.so" -o -name "*.dylib" \) -exec strip -x {} \; 2>/dev/null || true
    fi

    # 11. Remove .dist-info for packages we don't need metadata for
    echo "  - Removing unnecessary .dist-info..."
    # Keep mediapipe, numpy, pillow metadata
    find $SITE_PACKAGES -name "*.dist-info" \
        -not -name "mediapipe*" \
        -not -name "numpy*" \
        -not -name "Pillow*" \
        -type d -exec rm -rf {} + 2>/dev/null || true

    # 12. Remove .pyi stub files (type hints)
    echo "  - Removing type stub files..."
    find $SITE_PACKAGES -name "*.pyi" -delete 2>/dev/null || true

    # 13. Remove cached files
    echo "  - Removing cached files..."
    find "$BUILD_DIR/python" -name "*.cache" -delete 2>/dev/null || true

    echo "==> Optimization complete!"

else
    echo "ERROR: Virtual environment not found at $PROJECT_ROOT/venv"
    echo "Please run 'python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt' first"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Create bundle archive with better compression
BUNDLE_FILE="$OUTPUT_DIR/${ENGINE_ID}-${VERSION}.tar.gz"
echo "==> Creating bundle archive with optimized compression: $BUNDLE_FILE"

cd "$TEMP_DIR"
# Use -9 for maximum compression
tar -czf "$BUNDLE_FILE" --options='compression-level=9' "$ENGINE_ID" 2>/dev/null || tar -czf "$BUNDLE_FILE" "$ENGINE_ID"

# Calculate SHA256 checksum
echo "==> Calculating checksum..."
if command -v sha256sum &> /dev/null; then
    CHECKSUM=$(sha256sum "$BUNDLE_FILE" | awk '{print $1}')
elif command -v shasum &> /dev/null; then
    CHECKSUM=$(shasum -a 256 "$BUNDLE_FILE" | awk '{print $1}')
else
    echo "WARNING: Neither sha256sum nor shasum found, skipping checksum"
    CHECKSUM="unknown"
fi

# Get bundle size
BUNDLE_SIZE=$(stat -f%z "$BUNDLE_FILE" 2>/dev/null || stat -c%s "$BUNDLE_FILE" 2>/dev/null)
BUNDLE_SIZE_MB=$((BUNDLE_SIZE / 1024 / 1024))

# Clean up temp directory
rm -rf "$TEMP_DIR"

echo ""
echo "==> Bundle created successfully!"
echo "    File: $BUNDLE_FILE"
echo "    Size: ${BUNDLE_SIZE_MB}MB ($(numfmt --to=iec-i --suffix=B $BUNDLE_SIZE 2>/dev/null || echo "${BUNDLE_SIZE} bytes"))"
echo "    SHA256: $CHECKSUM"
echo ""
