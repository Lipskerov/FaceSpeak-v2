"""
FaceMetrics dataclass: 6 muscle channels, each 0.0–1.0 (post-calibration).
"""

from dataclasses import dataclass, field


@dataclass
class FaceMetrics:
    smile_width:   float = 0.0   # Zygomaticus major
    mouth_open:    float = 0.0   # Depressor labii
    eyebrow_raise: float = 0.0   # Frontalis
    lip_purse:     float = 0.0   # Orbicularis oris
    cheek_puff:    float = 0.0   # Buccinator (proxy)
    nose_wrinkle:  float = 0.0   # Nasalis

    def as_dict(self) -> dict:
        return {
            "smile_width":   self.smile_width,
            "mouth_open":    self.mouth_open,
            "eyebrow_raise": self.eyebrow_raise,
            "lip_purse":     self.lip_purse,
            "cheek_puff":    self.cheek_puff,
            "nose_wrinkle":  self.nose_wrinkle,
        }

    CHANNEL_NAMES = ["smile_width", "mouth_open", "eyebrow_raise",
                     "lip_purse", "cheek_puff", "nose_wrinkle"]
    CHANNEL_LABELS = ["Smile", "Mouth Open", "Eyebrow Raise",
                      "Lip Purse", "Cheek Puff", "Nose Wrinkle"]
