# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **detection engine** for behavioral monitoring using MediaPipe computer vision. The codebase implements a modular detection system for identifying specific behaviors (e.g., hand-near-mouth) from video frames. The detection logic is designed to be bundled, signed, and distributed as a secure, versioned package.

## Architecture

### Core Components

**Detection System** (Factory Pattern):

- `src/detection/base.py`: Abstract `BaseDetector` class defining the interface all detectors must implement
- `src/detection/factory.py`: Factory function `create_detector()` and registry `DETECTION_TYPES` for instantiating detectors
- `src/detection/hand_near_mouth.py`: Concrete detector implementation for hand-near-mouth behavior (nail biting detection)

**MediaPipe Engine** (Singleton Pattern):

- `src/mediapipe_engine.py`:
  - `MediaPipeEngine` class wraps MediaPipe's hand and face mesh models
  - Lazy initialization to defer heavy imports until first use
  - Singleton via `get_engine()` function
  - Provides utility methods: `get_mouth_center()`, `get_scale_factor()`, `get_mouth_openness()`
  - Returns `Detection` dataclass containing face and hand landmarks

**Backward-Compatible Facade**:

- `src/detection_logic.py`: `DetectionLogic` class provides a facade over the factory system for backward compatibility

### Data Flow

1. Frame(s) → `MediaPipeEngine.run()` → list of `Detection` objects (landmarks)
2. `Detection` → `BaseDetector.detect()` → (is_detected: bool, confidence: float)
3. Alternative: Frame → `BaseDetector.process_frame()` → (is_detected: bool, confidence: float)

### Adding New Detectors

1. Create new class in `src/detection/` inheriting from `BaseDetector`
2. Implement required methods: `__init__()`, `detect()`, `process_frame()`, `detection_type` property
3. Register in `DETECTION_TYPES` dict in `src/detection/factory.py`

## Development Commands

### Setup

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

### Running Detection

No standalone run command defined. This is a library/engine meant to be imported:

```python
from detection_logic import get_detection_logic
logic = get_detection_logic("hand_near_mouth")
is_detected, confidence = logic.process_frame(frame)
```

### Quick Start with Makefile

```bash
make help     # Show available commands
make bump     # Bump version (interactive)
make bundle   # Create distribution bundle
```

### Version Management

**Version is stored in `VERSION` file** - single source of truth for all version references.

Bump version:
```bash
make bump                          # Interactive selection
./scripts/bump.sh patch            # 1.0.0 -> 1.0.1
./scripts/bump.sh minor            # 1.0.0 -> 1.1.0
./scripts/bump.sh major            # 1.0.0 -> 2.0.0
./scripts/bump.sh 1.2.3            # Custom version
```

The bump script updates:
- `VERSION` file
- `scripts/bundle.sh` (reads VERSION on build)

### Building and Distribution

**Bundle the engine** (creates distributable tarball with code + venv):

```bash
make bundle                        # Using Makefile
./scripts/bundle.sh [output_dir]   # Direct script
```

Default output: `dist/hand_near_face-{VERSION}.tar.gz`

**Generate signing keys** (Ed25519):

```bash
./scripts/generate_signing_keys.sh [output_dir]
```

Default output: `keys/bundle_signing_key.{private,public}`

**Sign a bundle**:

```bash
./scripts/sign.sh <bundle_file> [private_key_file]
```

Creates `<bundle_file>.sig` with Ed25519 signature

## Important Constants

**Hand-Near-Mouth Detection** (`src/detection/hand_near_mouth.py`):

- `FINGERTIP_INDICES = [4, 8, 12, 16, 20]`: MediaPipe hand landmark indices for fingertips
- `MOUTH_OPEN_THRESHOLD = 0.30`: Skip detection if mouth is open (eating/talking)
- `HAND_MOUTH_DISTANCE_THRESHOLD = 0.35`: Normalized distance threshold for detection

## Security Model

This codebase implements a **signed bundle distribution system**:

- Bundles are cryptographically signed with Ed25519 private keys
- Public key should be embedded in consuming application for verification
- Private keys must never be committed to version control
- Signature verification prevents tampering with detection logic

## Dependencies

- `mediapipe==0.10.14`: Computer vision models for hand and face landmark detection
- `numpy==1.26.4`: Numerical operations for distance calculations
- `Pillow==10.4.0`: Image processing support

## Notes

- MediaPipe models are lazy-loaded on first use to reduce startup time
- All detectors use normalized coordinates and scale factors for device independence
- Logging is used throughout for debugging (`logging.getLogger(__name__)`)
- The engine uses singleton pattern to avoid reinitializing heavy MediaPipe models
