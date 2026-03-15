"""
Signal processing pipeline:
  raw distance → EMA → subtract calib_neutral → divide calib_range
  → clip(0,1) → hysteresis → FaceMetrics float

Calibration stores per-channel neutral and max values in progress.json.
"""

import numpy as np
from core.face_tracker import (
    EYE_P1, EYE_P2, MTH_PL, MTH_PR, MTH_U, MTH_D,
    MTH_INNER_U, MTH_INNER_D, NOSE, EYEB_L, EYEB_R,
    CHEEK_L, CHEEK_R, NOSE_BRIDGE, NOSE_TIP,
)
from core.metrics import FaceMetrics

# EMA smoothing factor (lower = smoother but slower)
EMA_ALPHA = 0.20

# Hysteresis thresholds
ACTIVATE_THRESH   = 0.35
DEACTIVATE_THRESH = 0.20

# Channels in order matching FaceMetrics
CHANNELS = FaceMetrics.CHANNEL_NAMES  # 6 names


class SignalProcessor:
    def __init__(self):
        self._ema = np.zeros(6, dtype=np.float64)
        self._active = np.zeros(6, dtype=bool)

        # Calibration — set by CalibrationWizard
        self.calib_neutral = np.zeros(6, dtype=np.float64)
        self.calib_range   = np.ones(6, dtype=np.float64)   # avoid /0
        self.calib_done    = False
        self.channel_active = np.ones(6, dtype=bool)  # channels with sufficient range

    # ------------------------------------------------------------------
    # Raw landmark → 6 raw distances (normalised by iris dist)
    # ------------------------------------------------------------------
    def _raw_distances(self, pts: np.ndarray) -> np.ndarray:
        def dist(i, j):
            return float(np.linalg.norm(pts[i, :2] - pts[j, :2]))

        d_eye = dist(EYE_P1, EYE_P2)
        if d_eye < 1e-6:
            return np.zeros(6)

        smile_width   = dist(MTH_PL, MTH_PR) / d_eye
        mouth_open    = dist(MTH_U, MTH_D) / d_eye
        # eyebrow: average of L/R brow to nose tip, normalised
        eyebrow_raise = (dist(NOSE, EYEB_L) + dist(NOSE, EYEB_R)) / (2 * d_eye)
        # lip purse: mouth NARROWS when pursing (61↔291 decreases).
        # Use 2.0 - mouth_width/d_eye so that pursing → higher raw value.
        # Neutral ≈ 2.0-1.3 = 0.7 ; max purse ≈ 2.0-0.8 = 1.2 → range ~0.5 ✓
        lip_purse = 2.0 - dist(MTH_PL, MTH_PR) / d_eye
        # cheek puff: outer cheek width increases when puffing
        cheek_puff    = dist(CHEEK_L, CHEEK_R) / d_eye
        # nose wrinkle: nose bridge moves closer to nose tip when wrinkling
        nose_wrinkle  = 1.0 - dist(NOSE_BRIDGE, NOSE_TIP) / d_eye

        return np.array([smile_width, mouth_open, eyebrow_raise,
                         lip_purse, cheek_puff, nose_wrinkle], dtype=np.float64)

    # ------------------------------------------------------------------
    # Apply EMA smoothing
    # ------------------------------------------------------------------
    def _smooth(self, raw: np.ndarray) -> np.ndarray:
        self._ema = EMA_ALPHA * raw + (1 - EMA_ALPHA) * self._ema
        return self._ema.copy()

    # ------------------------------------------------------------------
    # Map smoothed values to 0–1 using calibration
    # ------------------------------------------------------------------
    def _calibrate(self, smoothed: np.ndarray) -> np.ndarray:
        if not self.calib_done:
            # Before calibration: rough estimates so bars show live movement.
            # lip_purse neutral ≈ 0.7 (= 2.0 - 1.3); cheek_puff neutral ≈ 2.8
            neutral_est = np.array([1.2, 0.15, 2.0, 0.70, 2.8, 0.50])
            range_est   = np.array([0.6, 0.4,  0.5, 0.45, 0.4, 0.20])
            normed = (smoothed - neutral_est) / range_est
        else:
            normed = (smoothed - self.calib_neutral) / (self.calib_range + 1e-6)
        return np.clip(normed, 0.0, 1.0)

    # ------------------------------------------------------------------
    # Hysteresis: channel activates when > 0.35, deactivates when < 0.20
    # ------------------------------------------------------------------
    def _hysteresis(self, normed: np.ndarray) -> np.ndarray:
        for i in range(6):
            if not self._active[i] and normed[i] > ACTIVATE_THRESH:
                self._active[i] = True
            elif self._active[i] and normed[i] < DEACTIVATE_THRESH:
                self._active[i] = False
        # Return continuous value (not binary); active flag is for game logic
        return normed

    # ------------------------------------------------------------------
    # Main entry: landmarks → FaceMetrics
    # ------------------------------------------------------------------
    def process(self, pts: np.ndarray) -> FaceMetrics:
        raw      = self._raw_distances(pts)
        smoothed = self._smooth(raw)
        normed   = self._calibrate(smoothed)
        values   = self._hysteresis(normed)

        # Mask inactive channels
        values = values * self.channel_active

        return FaceMetrics(
            smile_width   = float(values[0]),
            mouth_open    = float(values[1]),
            eyebrow_raise = float(values[2]),
            lip_purse     = float(values[3]),
            cheek_puff    = float(values[4]),
            nose_wrinkle  = float(values[5]),
        )

    # ------------------------------------------------------------------
    # Calibration helpers (called by CalibrationWizard)
    # ------------------------------------------------------------------
    def set_calibration(self, neutral: np.ndarray, max_vals: np.ndarray):
        self.calib_neutral = neutral.copy()
        calib_range = max_vals - neutral
        # Use abs so channels where the metric *decreases* on activation
        # (e.g. lip_purse going further below neutral) still get activated.
        MIN_RANGE = 0.05
        self.channel_active = np.abs(calib_range) > MIN_RANGE
        # Keep signed range — normalization (smoothed - neutral) / range
        # handles negative ranges correctly: both numerator and denominator
        # are negative → positive result.
        self.calib_range = np.where(self.channel_active, calib_range, 1.0)
        self.calib_done = True
        print("[Calib] neutral:", np.round(neutral, 3))
        print("[Calib] range:  ", np.round(calib_range, 3))
        print("[Calib] active: ", self.channel_active)

    def get_smoothed_raw(self) -> np.ndarray:
        """Return current EMA values (raw, pre-calibration) for calibration capture."""
        return self._ema.copy()
