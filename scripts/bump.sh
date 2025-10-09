#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Files that need version updates
VERSION_FILE="$PROJECT_ROOT/VERSION"
BUNDLE_SCRIPT="$PROJECT_ROOT/scripts/bundle.sh"

# Check if VERSION file exists
if [ ! -f "$VERSION_FILE" ]; then
    echo -e "${RED}Error: VERSION file not found at $VERSION_FILE${NC}"
    exit 1
fi

# Get current version from VERSION file
CURRENT_VERSION=$(cat "$VERSION_FILE")

if [ -z "$CURRENT_VERSION" ]; then
    echo -e "${RED}Error: Could not determine current version${NC}"
    exit 1
fi

echo -e "${BLUE}Current version: ${GREEN}$CURRENT_VERSION${NC}"
echo ""

# Parse version components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Function to update version in files
update_version() {
    local new_version="$1"

    echo -e "${YELLOW}Updating to version: ${GREEN}$new_version${NC}"
    echo ""

    echo "$new_version" > "$VERSION_FILE"

    if [ -f "$BUNDLE_SCRIPT" ]; then
        sed -i.bak "s/^VERSION=\"[^\"]*\"/VERSION=\"$new_version\"/" "$BUNDLE_SCRIPT"
        rm "${BUNDLE_SCRIPT}.bak"
    fi

    echo -e "${GREEN}Version updated successfully${NC}"
}

# Interactive mode if no argument provided
if [ $# -eq 0 ]; then
    echo "Select version bump type:"
    echo "  1) Patch ($MAJOR.$MINOR.$PATCH -> $MAJOR.$MINOR.$((PATCH + 1)))"
    echo "  2) Minor ($MAJOR.$MINOR.$PATCH -> $MAJOR.$((MINOR + 1)).0)"
    echo "  3) Major ($MAJOR.$MINOR.$PATCH -> $((MAJOR + 1)).0.0)"
    echo "  4) Custom version"
    echo ""
    read -p "Enter choice (1-4): " choice

    case $choice in
        1)
            NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
            ;;
        2)
            NEW_VERSION="$MAJOR.$((MINOR + 1)).0"
            ;;
        3)
            NEW_VERSION="$((MAJOR + 1)).0.0"
            ;;
        4)
            read -p "Enter custom version (e.g., 1.2.3): " NEW_VERSION
            # Validate version format
            if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                echo -e "${RED}Error: Invalid version format. Please use X.Y.Z${NC}"
                exit 1
            fi
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
else
    # Command line argument provided
    case "$1" in
        patch)
            NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
            ;;
        minor)
            NEW_VERSION="$MAJOR.$((MINOR + 1)).0"
            ;;
        major)
            NEW_VERSION="$((MAJOR + 1)).0.0"
            ;;
        *)
            # Assume it's a custom version
            NEW_VERSION="$1"
            # Validate version format
            if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                echo -e "${RED}Error: Invalid version format. Use 'patch', 'minor', 'major' or X.Y.Z${NC}"
                exit 1
            fi
            ;;
    esac
fi

# Confirm before updating
echo ""
echo -e "${YELLOW}Version will be changed from ${RED}$CURRENT_VERSION${YELLOW} to ${GREEN}$NEW_VERSION${NC}"
read -p "Continue? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted${NC}"
    exit 1
fi

# Update the version
update_version "$NEW_VERSION"
