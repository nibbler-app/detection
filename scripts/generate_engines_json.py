#!/usr/bin/env python3
"""
Generate engines.json file for distribution

This script creates the engines.json manifest file that describes
available engine versions and download URLs.

Usage:
    python scripts/generate_engines_json.py [options]

Options:
    --version VERSION         Version to add (default: read from VERSION file)
    --base-url URL           Base URL for downloads (default: GitHub release URL)
    --dist-dir DIR           Distribution directory (default: dist/)
    --output FILE            Output file path (default: dist/engines.json)
    --platforms PLATFORMS    Comma-separated list of platforms (e.g., macos-arm64,windows-x64)
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes"""
    if file_path.exists():
        return file_path.stat().st_size
    return 0


def get_file_checksum(file_path: Path) -> str | None:
    """
    Get SHA256 checksum of a file.

    First tries to read from .sha256 file, then calculates directly.

    Args:
        file_path: Path to file

    Returns:
        SHA256 checksum as hex string, or None if file doesn't exist
    """
    if not file_path.exists():
        return None

    # Try to read from .sha256 file first
    sha256_file = Path(f"{file_path}.sha256")
    if sha256_file.exists():
        try:
            content = sha256_file.read_text().strip()
            # SHA256 files typically have format: "hash  filename"
            checksum = content.split()[0]
            return checksum
        except Exception as e:
            print(f"Warning: Could not read {sha256_file}: {e}", file=sys.stderr)

    # Calculate checksum directly
    try:
        sha256_hash = hashlib.sha256()
        with file_path.open("rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Warning: Could not calculate checksum for {file_path}: {e}", file=sys.stderr)
        return None


def generate_engines_json(
    version: str,
    base_url: str,
    dist_dir: Path,
    platforms: list[str],
    engine_name: str = "hand_near_face",
    engine_display_name: str = "Hand Near Face",
    engine_description: str = "Detects when a hand is near the face.",
) -> dict:
    """
    Generate engines.json structure

    Args:
        version: Engine version (e.g., "1.0.3")
        base_url: Base URL for downloads
        dist_dir: Directory containing built artifacts
        platforms: List of platform identifiers (e.g., ["macos-arm64"])
        engine_name: Internal engine name
        engine_display_name: Human-readable engine name
        engine_description: Engine description

    Returns:
        Dictionary representing engines.json structure
    """
    pub_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build platform data
    platform_data = {}
    for platform in platforms:
        # Construct artifact filename
        bundle_file = f"{engine_name}_{platform}-{version}.tar.gz"
        sig_file = f"{bundle_file}.sig"

        bundle_path = dist_dir / bundle_file
        sig_path = dist_dir / sig_file

        # Get file size
        size = get_file_size(bundle_path)

        if size == 0:
            print(f"Warning: Bundle not found or empty: {bundle_path}", file=sys.stderr)
            continue

        # Get checksum
        checksum = get_file_checksum(bundle_path)

        # Construct URLs
        bundle_url = f"{base_url}/{bundle_file}"
        sig_url = f"{base_url}/{sig_file}"

        platform_entry = {
            "url": bundle_url,
            "signature": sig_url,
            "size": size,
        }

        # Add checksum if available
        if checksum:
            platform_entry["checksum"] = checksum

        platform_data[platform] = platform_entry

    if not platform_data:
        raise ValueError("No valid platforms found with built artifacts")

    # Create release entry
    release = {
        "version": version,
        "pub_date": pub_date,
        "platforms": platform_data,
    }

    # Create engines.json structure
    engines_json = {
        engine_name: {
            "name": engine_display_name,
            "description": engine_description,
            "releases": [release],
        }
    }

    return engines_json


def merge_with_existing(
    new_data: dict,
    existing_file: Path,
    max_releases: int = 10,
) -> dict:
    """
    Merge new release data with existing engines.json

    Args:
        new_data: New engines.json data
        existing_file: Path to existing engines.json
        max_releases: Maximum number of releases to keep per engine

    Returns:
        Merged engines.json data
    """
    if not existing_file.exists():
        return new_data

    try:
        with open(existing_file, "r") as f:
            existing_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not read existing engines.json: {e}", file=sys.stderr)
        return new_data

    # Merge engine data
    for engine_name, engine_data in new_data.items():
        if engine_name not in existing_data:
            # New engine
            existing_data[engine_name] = engine_data
        else:
            # Existing engine - merge releases
            existing_releases = existing_data[engine_name].get("releases", [])
            new_releases = engine_data.get("releases", [])

            # Get all release versions
            existing_versions = {r["version"] for r in existing_releases}

            # Add new releases that don't exist
            for new_release in new_releases:
                if new_release["version"] not in existing_versions:
                    existing_releases.insert(0, new_release)  # Add at beginning

            # Sort by version (newest first) and limit
            existing_releases.sort(
                key=lambda r: [int(x) for x in r["version"].split(".")],
                reverse=True,
            )
            existing_data[engine_name]["releases"] = existing_releases[:max_releases]

    return existing_data


def main():
    parser = argparse.ArgumentParser(
        description="Generate engines.json for distribution"
    )
    parser.add_argument(
        "--version",
        help="Version to add (default: read from VERSION file)",
    )
    parser.add_argument(
        "--base-url",
        default="https://github.com/OWNER/REPO/releases/download/v{version}",
        help="Base URL for downloads (use {version} placeholder)",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path("dist"),
        help="Distribution directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/engines.json"),
        help="Output file path",
    )
    parser.add_argument(
        "--platforms",
        default="macos-arm64",
        help="Comma-separated list of platforms",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing engines.json",
    )
    parser.add_argument(
        "--max-releases",
        type=int,
        default=10,
        help="Maximum number of releases to keep (when merging)",
    )

    args = parser.parse_args()

    # Get version
    if args.version:
        version = args.version
    else:
        version_file = Path("VERSION")
        if version_file.exists():
            version = version_file.read_text().strip()
        else:
            print("Error: VERSION file not found and --version not specified", file=sys.stderr)
            sys.exit(1)

    # Format base URL with version
    base_url = args.base_url.format(version=version)

    # Parse platforms
    platforms = [p.strip() for p in args.platforms.split(",")]

    print(f"Generating engines.json for version {version}")
    print(f"Platforms: {', '.join(platforms)}")
    print(f"Base URL: {base_url}")

    # Generate engines.json
    try:
        engines_data = generate_engines_json(
            version=version,
            base_url=base_url,
            dist_dir=args.dist_dir,
            platforms=platforms,
        )

        # Merge with existing if requested
        if args.merge:
            engines_data = merge_with_existing(
                engines_data,
                args.output,
                max_releases=args.max_releases,
            )

        # Ensure output directory exists
        args.output.parent.mkdir(parents=True, exist_ok=True)

        # Write engines.json
        with open(args.output, "w") as f:
            json.dump(engines_data, f, indent=4)

        print(f"\nEngines.json written to: {args.output}")
        print(f"Size: {args.output.stat().st_size} bytes")

        # Print summary
        for engine_name, engine_data in engines_data.items():
            releases = engine_data.get("releases", [])
            print(f"\nEngine: {engine_name}")
            print(f"  Releases: {len(releases)}")
            for release in releases[:3]:  # Show first 3
                print(f"    - v{release['version']} ({len(release['platforms'])} platforms)")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
