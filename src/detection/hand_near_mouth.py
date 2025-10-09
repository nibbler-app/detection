import logging

import numpy as np

from detection.base import BaseDetector
from mediapipe_engine import Detection, get_engine

logger = logging.getLogger(__name__)

FINGERTIP_INDICES = [4, 8, 12, 16, 20]
MOUTH_OPEN_THRESHOLD = 0.30
HAND_MOUTH_DISTANCE_THRESHOLD = 0.35


class HandNearMouthDetector(BaseDetector):
    """Detector for hand-near-mouth behavior (nail biting, etc.)"""

    def __init__(self):
        super().__init__()
        self.engine = get_engine()

    @property
    def detection_type(self) -> str:
        return "hand_near_mouth"

    def detect(self, detection: Detection) -> tuple[bool, float]:
        """Check for hand near mouth in a single detection"""
        if not detection.face_landmarks or not detection.hand_landmarks:
            return False, 0.0

        face_landmarks = detection.face_landmarks

        mouth_openness = self.engine.get_mouth_openness(face_landmarks)
        if mouth_openness > MOUTH_OPEN_THRESHOLD:
            logger.debug(f"Skipping frame: mouth open (openness={mouth_openness:.2f})")
            return False, 0.0
        logger.debug(f"Mouth openess: {mouth_openness:.2f}")

        mouth_center = self.engine.get_mouth_center(face_landmarks)
        scale_factor = self.engine.get_scale_factor(face_landmarks)
        threshold = HAND_MOUTH_DISTANCE_THRESHOLD

        max_confidence = 0.0

        for hand in detection.hand_landmarks:
            for fingertip_idx in FINGERTIP_INDICES:
                fingertip = hand[fingertip_idx]

                distance = np.sqrt(
                    (fingertip[0] - mouth_center[0]) ** 2
                    + (fingertip[1] - mouth_center[1]) ** 2
                )

                normalized_distance = distance / scale_factor

                if normalized_distance < threshold:
                    confidence = 1.0 - (normalized_distance / threshold)
                    max_confidence = max(max_confidence, confidence)
                    logger.debug(
                        f"Fingertip {fingertip_idx} near mouth: "
                        f"distance={normalized_distance:.3f}, threshold={threshold}"
                    )

        is_detected = max_confidence > 0.0

        if is_detected:
            logger.info(
                f"Hand near mouth detected with confidence {max_confidence:.2f}"
            )

        return is_detected, max_confidence

    def process_frame(self, frame: np.ndarray) -> tuple[bool, float]:
        """Process a single frame for hand near mouth detection"""
        if frame is None or frame.size == 0:
            logger.warning("Invalid frame to process")
            return False, 0.0

        try:
            detections = self.engine.run([frame])  # MediaPipe still expects a list
            if detections and len(detections) > 0:
                return self.detect(detections[0])  # Use the first detection
            else:
                return False, 0.0
        except Exception as e:
            logger.error(f"Hand near mouth detection processing error: {e}")
            return False, 0.0
