"""
Session state: score, achievements, and persistence to data/progress.json.
"""

import json
import os
from datetime import date
from pathlib import Path

PROGRESS_FILE = Path(__file__).parent.parent / "data" / "progress.json"

ACHIEVEMENTS = {
    "first_smile":    {"label": "First Smile",    "desc": "Completed Level 1 for the first time"},
    "big_opener":     {"label": "Big Opener",      "desc": "Mouth fully open for 2 seconds"},
    "sky_high":       {"label": "Sky High",        "desc": "Balloon reached max height 3× in session"},
    "bubble_master":  {"label": "Bubble Master",   "desc": "Popped 20 bubbles in one session"},
    "all_muscles":    {"label": "All Muscles",     "desc": "All 6 channels activated in one session"},
    "five_day_streak":{"label": "5 Day Streak",    "desc": "Played 5 consecutive days"},
}


class Session:
    def __init__(self, profile: str = "default"):
        self.profile = profile
        self.score   = 0
        self.coins   = 0
        self.new_achievements: list[str] = []

        self._data = self._load()
        self._today = str(date.today())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self) -> dict:
        if PROGRESS_FILE.exists():
            try:
                return json.loads(PROGRESS_FILE.read_text())
            except Exception:
                pass
        return {}

    def _profile_data(self) -> dict:
        return self._data.setdefault(self.profile, {
            "achievements": [],
            "high_scores": {},
            "streak_dates": [],
            "calibration": None,
        })

    def save(self):
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROGRESS_FILE.write_text(json.dumps(self._data, indent=2))

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------
    def save_calibration(self, neutral: list, max_vals: list):
        self._profile_data()["calibration"] = {
            "neutral": neutral,
            "max_vals": max_vals,
        }
        self.save()

    def load_calibration(self) -> tuple | None:
        calib = self._profile_data().get("calibration")
        if calib:
            return calib["neutral"], calib["max_vals"]
        return None

    # ------------------------------------------------------------------
    # Achievements
    # ------------------------------------------------------------------
    def unlock_achievement(self, key: str):
        if key not in ACHIEVEMENTS:
            return
        earned = self._profile_data()["achievements"]
        if key not in earned:
            earned.append(key)
            self.new_achievements.append(key)
            self.save()

    def has_achievement(self, key: str) -> bool:
        return key in self._profile_data()["achievements"]

    def all_achievements(self) -> list[str]:
        return self._profile_data()["achievements"]

    # ------------------------------------------------------------------
    # High scores
    # ------------------------------------------------------------------
    def update_high_score(self, game_key: str, score: int):
        hs = self._profile_data()["high_scores"]
        if score > hs.get(game_key, 0):
            hs[game_key] = score
            self.save()

    def high_score(self, game_key: str) -> int:
        return self._profile_data()["high_scores"].get(game_key, 0)

    # ------------------------------------------------------------------
    # Streak
    # ------------------------------------------------------------------
    def record_play_today(self):
        dates = self._profile_data()["streak_dates"]
        if self._today not in dates:
            dates.append(self._today)
            dates.sort()
            # Keep last 30 days only
            self._profile_data()["streak_dates"] = dates[-30:]
            self.save()

        # Check 5-day streak
        from datetime import timedelta
        today_dt = date.fromisoformat(self._today)
        streak = 1
        for i in range(1, 6):
            d = str(today_dt - timedelta(days=i))
            if d in dates:
                streak += 1
            else:
                break
        if streak >= 5:
            self.unlock_achievement("five_day_streak")
