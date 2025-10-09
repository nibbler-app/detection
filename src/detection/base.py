from abc import ABC, abstractmethod

import numpy as np

from mediapipe_engine import Detection


class BaseDetector(ABC):
    """Base class for all detection types"""

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def detect(self, detection: Detection) -> tuple[bool, float]:
        """
        Process a single detection and return (is_detected, confidence)

        Args:
            detection: MediaPipe detection from a single frame

        Returns:
            Tuple of (is_detected: bool, confidence: float)
        """
        pass

    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> tuple[bool, float]:
        """
        Process a single frame and return detection result

        Args:
            frame: Image frame as numpy array

        Returns:
            Tuple of (is_detected: bool, confidence: float)
        """
        pass

    @property
    @abstractmethod
    def detection_type(self) -> str:
        """Return the type of detection this detector performs"""
        pass
