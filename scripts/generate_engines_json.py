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
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class PlatformData:
    url: str
    signature: str
    size: int
    checksum: str


@dataclass
class Release:
    version: str
    pub_date: str
    platforms: dict[str, PlatformData]


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes"""
    if file_path.exists():
        return file_path.stat().st_size
    return 0


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_engines_json(
    version: str,
    base_url: str,
    dist_dir: Path,
    platforms: list[str],
) -> Release:
    """
    Generate engines.json structure.
    """
    pub_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    platform_data: dict[str, PlatformData] = {}

    for platform in platforms:
        bundle_file = f"{platform}-{version}.tar.gz"
        sig_file = f"{bundle_file}.sig"
        bundle_path = dist_dir / bundle_file
        size = get_file_size(bundle_path)

        if size == 0:
            print(f"Warning: Bundle not found or empty: {bundle_path}", file=sys.stderr)
            continue

        checksum = calculate_checksum(bundle_path)

        platform_data[platform] = PlatformData(
            url=f"{base_url}/{bundle_file}",
            signature=f"{base_url}/{sig_file}",
            size=size,
            checksum=checksum,
        )

    if not platform_data:
        raise ValueError("No valid platforms found with built artifacts")

    return Release(
        version=version,
        pub_date=pub_date,
        platforms=platform_data,
    )


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

    args = parser.parse_args()

    # Get version
    if args.version:
        version = args.version
    else:
        version_file = Path("VERSION")
        if version_file.exists():
            version = version_file.read_text().strip()
        else:
            print(
                "Error: VERSION file not found and --version not specified",
                file=sys.stderr,
            )
            sys.exit(1)

    # Format base URL with version
    base_url = args.base_url.format(version=version)
    # Parse platforms
    platforms = [p.strip() for p in args.platforms.split(",")]

    print(f"Generating engines.json for version {version}")
    print(f"Platforms: {', '.join(platforms)}")
    print(f"Base URL: {base_url}")

    try:
        engines_data = generate_engines_json(
            version=version,
            base_url=base_url,
            dist_dir=args.dist_dir,
            platforms=platforms,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)

        with open(args.output, "w") as f:
            json.dump(asdict(engines_data), f, indent=4)

        print(f"\nEngines.json written to: {args.output}")
        print(f"Size: {args.output.stat().st_size} bytes")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
