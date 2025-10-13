"""
Sign a bundle with Ed25519 private key

This script signs a bundle archive using an Ed25519 private key.
The signature can be verified using the corresponding public key
embedded in the application.

Usage: python3 sign.py <bundle_file> [private_key_file]
"""

import argparse
import hashlib
import sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
except ImportError:
    print("ERROR: cryptography package is required", file=sys.stderr)
    print("Install it with: pip install cryptography", file=sys.stderr)
    sys.exit(1)


def load_private_key(key_file: Path) -> ed25519.Ed25519PrivateKey:
    """
    Load Ed25519 private key from hex file.

    Args:
        key_file: Path to private key file containing hex string

    Returns:
        Ed25519 private key object
    """
    try:
        # Read the private key hex
        private_key_hex = key_file.read_text().strip()

        # Convert hex to bytes
        private_key_bytes = bytes.fromhex(private_key_hex)

        # Load the private key
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)

        return private_key
    except Exception as e:
        print(f"ERROR: Failed to load private key: {e}", file=sys.stderr)
        sys.exit(1)


def sign_bundle(bundle_file: Path, private_key: ed25519.Ed25519PrivateKey) -> bytes:
    """
    Sign a bundle file with Ed25519 private key.

    Args:
        bundle_file: Path to bundle file to sign
        private_key: Ed25519 private key

    Returns:
        Signature bytes
    """
    try:
        # Read the bundle file
        bundle_data = bundle_file.read_bytes()

        # Hash the bundle data with SHA256 (to match Rust verification logic)
        bundle_hash = hashlib.sha256(bundle_data).digest()

        # Sign the hash (not the raw data)
        signature = private_key.sign(bundle_hash)

        return signature
    except Exception as e:
        print(f"ERROR: Failed to sign bundle: {e}", file=sys.stderr)
        sys.exit(1)


def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to file

    Returns:
        Hex string of checksum
    """
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Sign a bundle with Ed25519 private key"
    )
    parser.add_argument(
        "bundle_file",
        help="Path to bundle file to sign"
    )
    parser.add_argument(
        "private_key_file",
        nargs="?",
        default=None,
        help="Path to private key file (default: ../keys/bundle_signing_key.private relative to script)"
    )

    args = parser.parse_args()

    # Parse bundle file path
    bundle_file = Path(args.bundle_file)
    if not bundle_file.exists():
        print(f"ERROR: Bundle file not found: {bundle_file}", file=sys.stderr)
        sys.exit(1)

    # Determine private key file path
    if args.private_key_file:
        private_key_file = Path(args.private_key_file)
    else:
        script_dir = Path(__file__).parent
        private_key_file = script_dir.parent / "keys" / "bundle_signing_key.private"

    if not private_key_file.exists():
        print(f"ERROR: Private key file not found: {private_key_file}", file=sys.stderr)
        print("Generate keys first: python3 scripts/generate_signing_keys.py", file=sys.stderr)
        sys.exit(1)

    print(f"==> Signing bundle: {bundle_file}")

    # Load private key
    private_key = load_private_key(private_key_file)

    # Sign the bundle
    signature = sign_bundle(bundle_file, private_key)

    # Convert signature to hex
    signature_hex = signature.hex()
    print(f"Signature: {signature_hex}")

    # Save signature to file
    signature_file = Path(f"{bundle_file}.sig")
    signature_file.write_text(signature_hex)
    print(f"Signature saved to: {signature_file}")

    # Calculate and display checksum
    print()
    print("==> Bundle checksum:")
    checksum = calculate_checksum(bundle_file)
    print(f"{checksum}  {bundle_file.name}")


if __name__ == "__main__":
    main()
