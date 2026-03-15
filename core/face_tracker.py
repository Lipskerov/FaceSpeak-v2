"""
MediaPipe FaceMesh wrapper — returns 478-landmark array each frame.
"""

import cv2
import numpy as np
import mediapipe as mp

# Landmark indices
EYE_P1 = 468   # left iris center
EYE_P2 = 473   # right iris center
MTH_PL = 61    # mouth left corner
MTH_PR = 291   # mouth right corner
MTH_U  = 16    # upper lip outer
MTH_D  = 11    # lower lip outer
MTH_INNER_U = 13   # inner upper lip
MTH_INNER_D = 14   # inner lower lip
NOSE   = 4     # nose tip
EYEB_L = 55    # left eyebrow inner
EYEB_R = 336   # right eyebrow inner
CHEEK_L = 234  # outer left cheek
CHEEK_R = 454  # outer right cheek
NOSE_BRIDGE = 168  # nose bridge
NOSE_TIP = 6       # nose tip (forehead ref)


class FaceTracker:
    def __init__(self):
        mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self.last_landmarks: np.ndarray | None = None  # shape (478, 3)

    def process(self, bgr_frame: np.ndarray) -> np.ndarray | None:
        """
        Takes a BGR frame, returns (478, 3) float32 array in pixel coords,
        or None if no face detected.
        """
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return None

        H, W = bgr_frame.shape[:2]
        lm = results.multi_face_landmarks[0]
        pts = np.array([[W * l.x, H * l.y, l.z] for l in lm.landmark], dtype=np.float32)
        self.last_landmarks = pts
        return pts

    def close(self):
        self.face_mesh.close()
