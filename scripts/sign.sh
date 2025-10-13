#!/bin/bash
# Sign a bundle with Ed25519 private key
#
# This script signs a bundle archive using an Ed25519 private key.
# The signature can be verified using the corresponding public key
# embedded in the application.
#
# Usage: ./sign_bundle.sh <bundle_file> [private_key_file]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_FILE="$1"
PRIVATE_KEY_FILE="${2:-$SCRIPT_DIR/../keys/bundle_signing_key.private}"

if [ -z "$BUNDLE_FILE" ]; then
    echo "ERROR: Bundle file path required"
    echo "Usage: $0 <bundle_file> [private_key_file]"
    exit 1
fi

if [ ! -f "$BUNDLE_FILE" ]; then
    echo "ERROR: Bundle file not found: $BUNDLE_FILE"
    exit 1
fi

if [ ! -f "$PRIVATE_KEY_FILE" ]; then
    echo "ERROR: Private key file not found: $PRIVATE_KEY_FILE"
    echo "Generate keys first: ./scripts/generate_signing_keys.sh"
    exit 1
fi

echo "==> Signing bundle: $BUNDLE_FILE"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 is required but not found"
    exit 1
fi

# Export variables for Python script
export BUNDLE_FILE
export PRIVATE_KEY_FILE

# Sign the bundle using Python cryptography library
python3 << 'EOF'
import sys
import os
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Read inputs from environment
bundle_file = os.environ.get('BUNDLE_FILE')
private_key_file = os.environ.get('PRIVATE_KEY_FILE')

# Read the bundle file
with open(bundle_file, 'rb') as f:
    bundle_data = f.read()

# Read the private key hex
with open(private_key_file, 'r') as f:
    private_key_hex = f.read().strip()

# Convert hex to bytes
private_key_bytes = bytes.fromhex(private_key_hex)

# Load the private key
private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)

# Sign the bundle data
signature = private_key.sign(bundle_data)

# Convert signature to hex
signature_hex = signature.hex()

# Output the signature
print(f"Signature: {signature_hex}")

# Save signature to file
signature_file = f"{bundle_file}.sig"
with open(signature_file, 'w') as f:
    f.write(signature_hex)

print(f"Signature saved to: {signature_file}")
EOF

# Calculate SHA256 checksum for reference
echo ""
echo "==> Bundle checksum:"
if command -v sha256sum &> /dev/null; then
    sha256sum "$BUNDLE_FILE"
elif command -v shasum &> /dev/null; then
    shasum -a 256 "$BUNDLE_FILE"
else
    echo "WARNING: Neither sha256sum nor shasum found"
fi
