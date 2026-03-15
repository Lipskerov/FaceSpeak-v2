"""
Game 1 — "Journey to the Star"
Migrated from v1 game_panel.py, rewritten for pygame.

Controls (sustained thresholds):
  mouth_open    ≥ 0.35 → boy walks right
  smile_width   ≥ 0.35 → balloon rises, lifting boy over hills
  eyebrow_raise ≥ 0.35 → boy jumps (clears gaps)

3 Levels:
  1 — flat path, mouth_open only, 5 steps to star
  2 — one hill, mouth_open + smile
  3 — hill + gap, all three muscles
"""

import os
import pygame
from games.base_game import BaseGame
from core.metrics import FaceMetrics
from core.session import Session

ASSETS = os.path.join(os.path.dirname(__file__), "..", "resources")

# Game constants
BOY_WALK_SPEED  = 120   # px / second when mouth open
BALLOON_RISE    = 180   # px / second when smiling
BALLOON_FALL    = 80    # px / second when not smiling
BOY_JUMP_VEL    = -320  # px / second initial jump velocity
GRAVITY         = 600   # px / second²
GOAL_X_FRAC     = 0.80  # fraction of screen_w = star/goal position


def load_img(name, w=None, h=None):
    path = os.path.join(ASSETS, name)
    img = pygame.image.load(path).convert_alpha()
    if w and h:
        img = pygame.transform.scale(img, (w, h))
    return img


class Level:
    """Describes terrain for a single level."""
    def __init__(self, ground_y: int, screen_w: int, screen_h: int,
                 hills: list, gaps: list):
        """
        hills: list of (x_center, width, height) tuples
        gaps:  list of (x_start, width) tuples
        """
        self.ground_y = ground_y
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.hills = hills
        self.gaps  = gaps

    def ground_at(self, x: float) -> float:
        """Return ground y at position x (accounting for hills/gaps)."""
        # Check gaps — in a gap the boy falls
        for gx, gw in self.gaps:
            if gx <= x <= gx + gw:
                return self.screen_h + 100  # below screen = fell

        # Check hills
        for hx, hw, hh in self.hills:
            if abs(x - hx) < hw / 2:
                return self.ground_y - hh

        return self.ground_y


class GameJourney(BaseGame):
    def __init__(self, screen_w, screen_h, session: Session, level: int = 1):
        super().__init__(screen_w, screen_h, session)
        self.level_num = level
        self._assets_loaded = False
        self.reset()

    def _ensure_assets(self):
        if self._assets_loaded:
            return
        self.bg_img  = load_img("bg_final_s.png",
                                w=self.screen_w, h=self.screen_h)
        self.boy_img = load_img("boy_start.png", w=80, h=80)
        self.balloon_img = load_img("balloon.png", w=70, h=140)
        self.win_img = load_img("win.png")
        self.coins_img = load_img("coins.png", w=60, h=60)
        self._assets_loaded = True

    def reset(self):
        self._assets_loaded = False
        self.completed   = False
        self.coins_earned = 0
        self._win_timer  = 0.0

        # Boy state
        self.boy_x  = 60.0
        self.boy_y  = 0.0   # set properly after level init
        self.boy_vy = 0.0
        self.on_ground = True

        # Balloon state (hovers above boy)
        self.balloon_visible = True
        self.balloon_y_offset = -160.0   # relative to boy_y (negative = above)
        self.balloon_hold_height = 0.0   # max height bonus from smiling

        # Level terrain
        gnd = int(self.screen_h * 0.72)
        sw  = self.screen_w
        sh  = self.screen_h

        if self.level_num == 1:
            self._level = Level(gnd, sw, sh, hills=[], gaps=[])
            self._goal_x = sw * 0.82
            self._muscles_needed = {"mouth_open"}
        elif self.level_num == 2:
            self._level = Level(gnd, sw, sh,
                                hills=[(int(sw * 0.55), 120, 80)], gaps=[])
            self._goal_x = sw * 0.82
            self._muscles_needed = {"mouth_open", "smile_width"}
        else:
            self._level = Level(gnd, sw, sh,
                                hills=[(int(sw * 0.45), 120, 80)],
                                gaps=[(int(sw * 0.62), 80)])
            self._goal_x = sw * 0.85
            self._muscles_needed = {"mouth_open", "smile_width", "eyebrow_raise"}

        self.boy_y = float(self._level.ground_at(self.boy_x) - 80)

        # Achievement tracking
        self._balloon_max_rises = 0
        self._balloon_prev_y = self.balloon_y_offset
        self._channels_seen: set = set()

    @property
    def game_key(self):
        return f"journey_l{self.level_num}"

    def update(self, metrics: FaceMetrics, dt: float):
        self._ensure_assets()
        if self.completed:
            self._win_timer += dt
            return

        # Track channels for achievement
        if metrics.mouth_open    > 0.35: self._channels_seen.add("mouth_open")
        if metrics.smile_width   > 0.35: self._channels_seen.add("smile_width")
        if metrics.eyebrow_raise > 0.35: self._channels_seen.add("eyebrow_raise")
        if metrics.lip_purse     > 0.35: self._channels_seen.add("lip_purse")
        if metrics.cheek_puff    > 0.35: self._channels_seen.add("cheek_puff")
        if metrics.nose_wrinkle  > 0.35: self._channels_seen.add("nose_wrinkle")

        # --- Boy horizontal movement ---
        if metrics.mouth_open >= 0.35:
            self.boy_x += BOY_WALK_SPEED * dt

        # --- Jump (eyebrow) ---
        if metrics.eyebrow_raise >= 0.35 and self.on_ground:
            self.boy_vy = BOY_JUMP_VEL

        # --- Gravity & ground collision ---
        ground_y = self._level.ground_at(self.boy_x)
        self.boy_vy += GRAVITY * dt
        self.boy_y  += self.boy_vy * dt

        if self.boy_y >= ground_y - 80:
            self.boy_y  = ground_y - 80
            self.boy_vy = 0.0
            self.on_ground = True
        else:
            self.on_ground = False

        # --- Balloon vertical ---
        if metrics.smile_width >= 0.35:
            # Balloon pulls boy up
            self.balloon_y_offset -= BALLOON_RISE * dt
            # Balloon lift: override ground collision if balloon is high
            if self.balloon_y_offset < -200:
                lift = (-self.balloon_y_offset - 200) * 0.6
                self.boy_y -= lift * dt * 60
        else:
            # Balloon slowly descends back
            target_offset = -160.0
            if self.balloon_y_offset < target_offset:
                self.balloon_y_offset += BALLOON_FALL * dt
                self.balloon_y_offset = min(self.balloon_y_offset, target_offset)

        # Track balloon height rises for achievement
        if self.balloon_y_offset < self._balloon_prev_y - 60:
            self._balloon_max_rises += 1
        self._balloon_prev_y = self.balloon_y_offset

        # Clamp balloon
        self.balloon_y_offset = max(self.balloon_y_offset, -280.0)

        # Clamp boy to screen
        self.boy_x = max(40.0, min(self.boy_x, self.screen_w - 60.0))
        self.boy_y = max(0.0, self.boy_y)

        # --- Win condition ---
        if self.boy_x >= self._goal_x:
            self._complete()

    def _complete(self):
        self.completed    = True
        self.coins_earned = 10 * self.level_num
        self.session.score += self.coins_earned
        self.session.update_high_score(self.game_key, self.session.score)
        self.session.record_play_today()

        # Achievements
        if self.level_num == 1:
            self.session.unlock_achievement("first_smile")
        if self._balloon_max_rises >= 3:
            self.session.unlock_achievement("sky_high")
        if len(self._channels_seen) >= 6:
            self.session.unlock_achievement("all_muscles")

    def draw(self, surface: pygame.Surface):
        self._ensure_assets()

        # Background
        surface.blit(self.bg_img, (0, 0))

        # Draw hills
        for hx, hw, hh in self._level.hills:
            hill_rect = pygame.Rect(
                int(hx - hw // 2), int(self._level.ground_y - hh),
                hw, hh
            )
            pygame.draw.ellipse(surface, (80, 140, 60), hill_rect)

        # Draw gaps
        for gx, gw in self._level.gaps:
            gap_rect = pygame.Rect(int(gx), int(self._level.ground_y),
                                   gw, self.screen_h - self._level.ground_y)
            pygame.draw.rect(surface, (30, 30, 50), gap_rect)

        # Draw goal star
        font = pygame.font.SysFont(None, 60)
        star = font.render("⭐", True, (255, 215, 0))
        surface.blit(star, (int(self._goal_x - 20), self._level.ground_y - 80))

        # Balloon (above boy)
        bx = int(self.boy_x + 5)
        by = int(self.boy_y + self.balloon_y_offset)
        surface.blit(self.balloon_img, (bx, by))

        # Boy
        surface.blit(self.boy_img, (int(self.boy_x), int(self.boy_y)))

        # Ground line
        pygame.draw.line(surface, (100, 70, 30),
                         (0, self._level.ground_y),
                         (self.screen_w, self._level.ground_y), 3)

        # Win overlay
        if self.completed:
            # Coins burst animation (simple)
            for i in range(min(int(self._win_timer * 8), 15)):
                cx = 200 + i * 40
                cy = 100 + (i % 3) * 50
                surface.blit(self.coins_img, (cx, cy))
            # Win image
            wx = self.screen_w // 2 - self.win_img.get_width() // 2
            wy = self.screen_h // 2 - self.win_img.get_height() // 2
            surface.blit(self.win_img, (wx, wy))

        # Level indicator
        font_sm = pygame.font.SysFont(None, 28)
        lbl = font_sm.render(f"Level {self.level_num}", True, (255, 255, 255))
        surface.blit(lbl, (10, 10))
