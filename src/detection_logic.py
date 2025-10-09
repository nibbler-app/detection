"""
Detection logic module - Main interface for detection functionality

This module provides backward compatibility while delegating to the new modular detection system.
"""

import logging

import numpy as np

from detection.factory import create_detector
from mediapipe_engine import Detection

logger = logging.getLogger(__name__)


class DetectionLogic:
    """
    Main detection logic class - provides backward compatibility

    This class wraps the new modular detection system while maintaining
    the same interface for existing code.
    """

    def __init__(
        self,
        detection_type: str = "hand_near_mouth",
    ):
        self.detector = create_detector(detection_type)

    @property
    def detection_type(self) -> str:
        """Get the current detection type"""
        return self.detector.detection_type

    def detect_single(self, detection: Detection) -> tuple[bool, float]:
        """Process a single detection"""
        return self.detector.detect(detection)

    def process_frame(self, frame: np.ndarray) -> tuple[bool, float]:
        """Process a single frame for detection"""
        return self.detector.process_frame(frame)


_logic_instance: DetectionLogic | None = None


def get_detection_logic(detection_type: str = "hand_near_mouth") -> DetectionLogic:
    """
    Get a DetectionLogic instance with specified detection type

    Args:
        detection_type: Type of detection to perform (default: "hand_near_mouth")

    Returns:
        DetectionLogic instance
    """
    global _logic_instance

    # Create new instance if none exists or detection type changed
    if _logic_instance is None or _logic_instance.detection_type != detection_type:
        _logic_instance = DetectionLogic(detection_type)

    return _logic_instance
