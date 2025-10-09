import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    face_landmarks: list | None = None
    hand_landmarks: list | None = None
    confidence: float = 0.0


class MediaPipeEngine:
    def __init__(self):
        self.mp_hands = None
        self.mp_face_mesh = None

        self.hands = None
        self.face_mesh = None
        self._initialized = False

    def _lazy_init(self):
        if self._initialized:
            return

        logger.info("Initializing MediaPipe models...")

        # Lazy import MediaPipe modules only when first needed
        if self.mp_hands is None:
            logger.info("Importing MediaPipe hands module...")
            import mediapipe.python.solutions.hands as hands

            self.mp_hands = hands

        if self.mp_face_mesh is None:
            logger.info("Importing MediaPipe face_mesh module...")
            import mediapipe.python.solutions.face_mesh as face_mesh

            self.mp_face_mesh = face_mesh

        try:
            self.hands = self.mp_hands.Hands(
                static_image_mode=True,
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("Hands model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize hands model: {e}")
            raise

        try:
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            logger.info("Face mesh model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize face mesh model: {e}")
            raise

        self._initialized = True
        logger.info("All MediaPipe models initialized successfully")

    def run(self, frames: list[np.ndarray]) -> list[Detection]:
        self._lazy_init()

        assert self.hands is not None
        assert self.face_mesh is not None

        detections = []

        for frame in frames:
            detection = Detection()

            face_results = self.face_mesh.process(frame)
            multi_face_landmarks = face_results.multi_face_landmarks  # pyright: ignore
            if multi_face_landmarks:
                face_landmarks = multi_face_landmarks[0]
                detection.face_landmarks = [(lm.x, lm.y, lm.z) for lm in face_landmarks.landmark]

            hand_results = self.hands.process(frame)
            multi_hand_landmarks = hand_results.multi_hand_landmarks  # pyright: ignore
            if multi_hand_landmarks:
                detection.hand_landmarks = []
                for hand_landmarks in multi_hand_landmarks:
                    hand_data = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
                    detection.hand_landmarks.append(hand_data)

            detections.append(detection)

        return detections

    def get_mouth_center(
        self, face_landmarks: list[tuple[float, float, float]]
    ) -> tuple[float, float]:
        upper_lip = face_landmarks[13]
        lower_lip = face_landmarks[14]
        return ((upper_lip[0] + lower_lip[0]) / 2, (upper_lip[1] + lower_lip[1]) / 2)

    def get_scale_factor(self, face_landmarks: list[tuple[float, float, float]]) -> float:
        left_eye = face_landmarks[33]
        right_eye = face_landmarks[263]

        inter_ocular_distance = np.sqrt(
            (right_eye[0] - left_eye[0]) ** 2 + (right_eye[1] - left_eye[1]) ** 2
        )

        return float(max(inter_ocular_distance, 0.05))

    def get_mouth_openness(self, face_landmarks: list[tuple[float, float, float]]) -> float:
        upper_lip = face_landmarks[13]
        lower_lip = face_landmarks[14]

        scale = self.get_scale_factor(face_landmarks)
        mouth_distance = np.sqrt(
            (upper_lip[0] - lower_lip[0]) ** 2 + (upper_lip[1] - lower_lip[1]) ** 2
        )

        return float(mouth_distance / scale)

    def __del__(self):
        if self.hands:
            self.hands.close()
        if self.face_mesh:
            self.face_mesh.close()


_engine_instance: MediaPipeEngine | None = None


def get_engine() -> MediaPipeEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MediaPipeEngine()
    return _engine_instance
