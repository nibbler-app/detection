"""
Generate Ed25519 signing keys for bundle verification

This script generates a public/private key pair for signing engine bundles.
The private key should be kept secure and used only for signing bundles.
The public key should be embedded in the application for verification.

Usage: python3 generate_signing_keys.py [output_dir]
"""

import argparse
import sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("ERROR: cryptography package is required", file=sys.stderr)
    print("Install it with: pip install cryptography", file=sys.stderr)
    sys.exit(1)


def generate_keys(output_dir: Path) -> tuple[str, str]:
    """
    Generate Ed25519 key pair and return as hex strings.

    Args:
        output_dir: Directory to save the keys

    Returns:
        Tuple of (private_key_hex, public_key_hex)
    """
    # Generate private key
    private_key = ed25519.Ed25519PrivateKey.generate()

    # Generate public key
    public_key = private_key.public_key()

    # Serialize private key
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    # Convert to hex
    private_hex = private_bytes.hex()
    public_hex = public_bytes.hex()

    return private_hex, public_hex


def save_keys(output_dir: Path, private_hex: str, public_hex: str) -> tuple[Path, Path]:
    """
    Save keys to files with appropriate permissions.

    Args:
        output_dir: Directory to save the keys
        private_hex: Private key as hex string
        public_hex: Public key as hex string
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    private_key_path = output_dir / "bundle_signing_key.private"
    public_key_path = output_dir / "bundle_signing_key.public"

    # Write private key
    private_key_path.write_text(private_hex)
    # Set restrictive permissions on private key (owner read/write only)
    private_key_path.chmod(0o600)

    # Write public key
    public_key_path.write_text(public_hex)
    # Set public key permissions (owner read/write, others read)
    public_key_path.chmod(0o644)

    return private_key_path, public_key_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate Ed25519 signing keys for bundle verification"
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="Output directory for keys (default: ../keys relative to script)"
    )

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        script_dir = Path(__file__).parent
        output_dir = script_dir.parent / "keys"

    print("==> Generating Ed25519 signing keys")

    # Generate keys
    private_hex, public_hex = generate_keys(output_dir)

    # Save keys
    private_key_path, public_key_path = save_keys(output_dir, private_hex, public_hex)

    # Print keys
    print(f"Private key: {private_hex}")
    print(f"Public key: {public_hex}")
    print()
    print("==> Keys generated successfully!")
    print(f"    Private key: {private_key_path}")
    print(f"    Public key:  {public_key_path}")
    print()
    print("IMPORTANT:")
    print("  - Keep the private key secure and never commit it to version control")
    print("  - Add 'keys/' to your .gitignore")
    print("  - The public key should be embedded in api/src/bundle_manager.rs")
    print()
    print("To embed the public key in the application:")
    print(f"  1. Copy the public key hex from: {public_key_path}")
    print("  2. Update PUBLIC_KEY_HEX in api/src/bundle_manager.rs")


if __name__ == "__main__":
    main()
