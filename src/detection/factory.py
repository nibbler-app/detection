"""Factory for creating detection instances"""

from detection.base import BaseDetector
from detection.hand_near_mouth import HandNearMouthDetector

# Registry of available detection types
DETECTION_TYPES: dict[str, type[BaseDetector]] = {
    "hand_near_mouth": HandNearMouthDetector,
}


def create_detector(detection_type: str = "hand_near_mouth") -> BaseDetector:
    """
    Create a detector instance based on detection type.
    Raises:
        ValueError: If detection_type is not supported
    """
    if detection_type not in DETECTION_TYPES:
        available_types = ", ".join(DETECTION_TYPES.keys())
        raise ValueError(
            f"Unsupported detection type '{detection_type}'. Available types: {available_types}"
        )

    detector_class = DETECTION_TYPES[detection_type]
    return detector_class()


def get_available_detection_types() -> list[str]:
    """Return list of available detection types"""
    return list(DETECTION_TYPES.keys())
