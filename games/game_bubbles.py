"""
Game 2 — "Bubble Garden"
New game using lip_purse + smile_width.

Controls:
  lip_purse ≥ 0.4 sustained for hold_duration → spawn bubble
  smile_width ≥ 0.5 → pop nearest floating bubble → coins

4 flowers = WIN (5 pops per flower watering)
"""

import os
import math
import random
import pygame
from games.base_game import BaseGame
from core.metrics import FaceMetrics
from core.session import Session

ASSETS = os.path.join(os.path.dirname(__file__), "..", "resources")

# Hold durations per difficulty
HOLD_DURATIONS = {"easy": 1.5, "medium": 1.0, "hard": 0.7}
BUBBLE_SPEED   = 80   # px / second upward
BUBBLE_WOBBLE  = 30   # px horizontal wobble amplitude
N_FLOWERS      = 4
POPS_PER_FLOWER= 5

BUBBLE_COLORS = [
    (173, 216, 255, 160),
    (173, 255, 200, 160),
    (255, 220, 173, 160),
    (220, 173, 255, 160),
]


class Bubble:
    def __init__(self, x: float, y: float, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = random.randint(22, 36)
        self.age = 0.0
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.alive = True

    def update(self, dt: float):
        self.age += dt
        self.y -= BUBBLE_SPEED * dt
        self.x += math.sin(self.age * 2 + self.wobble_phase) * WOBBLE_SCALE * dt

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return
        bubble_surf = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4),
                                     pygame.SRCALPHA)
        pygame.draw.circle(bubble_surf, self.color,
                           (self.radius + 2, self.radius + 2), self.radius)
        # Highlight
        pygame.draw.circle(bubble_surf, (255, 255, 255, 80),
                           (self.radius, self.radius - 4), self.radius // 3)
        pygame.draw.circle(bubble_surf, (200, 200, 255, 120),
                           (self.radius + 2, self.radius + 2), self.radius, 2)
        surface.blit(bubble_surf, (int(self.x - self.radius - 2),
                                   int(self.y - self.radius - 2)))


WOBBLE_SCALE = 25.0


class Flower:
    def __init__(self, x: int, y: int, color: tuple):
        self.x = x
        self.y = y
        self.color = color
        self.pops = 0
        self.watered = False

    def water(self):
        self.pops += 1
        if self.pops >= POPS_PER_FLOWER:
            self.watered = True

    def draw(self, surface: pygame.Surface):
        # Stem
        pygame.draw.line(surface, (60, 160, 60),
                         (self.x, self.y), (self.x, self.y + 60), 4)
        # Leaves
        pygame.draw.ellipse(surface, (80, 180, 80),
                            (self.x - 20, self.y + 20, 20, 10))
        pygame.draw.ellipse(surface, (80, 180, 80),
                            (self.x + 2, self.y + 30, 20, 10))

        # Petals
        bloom_color = self.color if self.watered else (200, 200, 200)
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            px = self.x + int(math.cos(rad) * 14)
            py = self.y + int(math.sin(rad) * 14)
            pygame.draw.circle(surface, bloom_color, (px, py), 10)

        # Center
        pygame.draw.circle(surface, (255, 230, 100), (self.x, self.y), 10)

        # Progress dots
        for i in range(POPS_PER_FLOWER):
            dot_color = (100, 220, 100) if i < self.pops else (180, 180, 180)
            pygame.draw.circle(surface, dot_color,
                               (self.x - 10 + i * 5, self.y - 18), 3)


class GameBubbles(BaseGame):
    def __init__(self, screen_w, screen_h, session: Session, difficulty: str = "easy"):
        super().__init__(screen_w, screen_h, session)
        self.difficulty   = difficulty
        self.hold_duration = HOLD_DURATIONS.get(difficulty, 1.5)
        self._assets_loaded = False
        self.reset()

    def _ensure_assets(self):
        if self._assets_loaded:
            return
        self.coins_img = pygame.image.load(
            os.path.join(ASSETS, "coins.png")).convert_alpha()
        self.coins_img = pygame.transform.scale(self.coins_img, (50, 50))
        self._assets_loaded = True

    def reset(self):
        self._assets_loaded = False
        self.completed    = False
        self.coins_earned = 0
        self._win_timer   = 0.0

        self.bubbles: list[Bubble] = []
        self._purse_hold   = 0.0   # seconds lip_purse sustained
        self._total_pops   = 0
        self._pop_particles: list  = []  # (x, y, timer)
        self._coins_display: list  = []  # (x, y, timer)

        # Spawn flowers along the bottom
        n = N_FLOWERS
        flower_colors = [(255, 100, 100), (255, 180, 60),
                         (100, 180, 255), (180, 100, 255)]
        ground_y = int(self.screen_h * 0.88)
        xs = [int(self.screen_w * (i + 1) / (n + 1)) for i in range(n)]
        self.flowers = [Flower(x, ground_y, c)
                        for x, c in zip(xs, flower_colors)]

    @property
    def game_key(self):
        return "bubbles"

    def update(self, metrics: FaceMetrics, dt: float):
        self._ensure_assets()
        if self.completed:
            self._win_timer += dt
            return

        # --- Lip purse hold tracking ---
        if metrics.lip_purse >= 0.4:
            self._purse_hold += dt
            if self._purse_hold >= self.hold_duration:
                self._spawn_bubble()
                self._purse_hold = 0.0  # reset after spawn
        else:
            self._purse_hold = max(0.0, self._purse_hold - dt * 2)

        # --- Bubble movement ---
        for b in self.bubbles:
            b.update(dt)

        # Remove off-screen bubbles
        self.bubbles = [b for b in self.bubbles
                        if b.alive and b.y > -60]

        # --- Pop on smile ---
        if metrics.smile_width >= 0.5 and self.bubbles:
            # Pop the lowest bubble (easiest to aim for CP kids)
            lowest = max(self.bubbles, key=lambda b: b.y)
            self._pop_bubble(lowest)

        # --- Update pop particles ---
        self._pop_particles = [(x, y, t - dt)
                               for x, y, t in self._pop_particles if t > 0]
        self._coins_display  = [(x, y, t - dt)
                                for x, y, t in self._coins_display if t > 0]

        # --- Win condition ---
        if all(f.watered for f in self.flowers):
            self._complete()

    def _spawn_bubble(self):
        # Spawn near center-bottom of screen
        x = self.screen_w // 2 + random.randint(-60, 60)
        y = self.screen_h * 0.75
        color = random.choice(BUBBLE_COLORS)
        self.bubbles.append(Bubble(x, y, color))

    def _pop_bubble(self, bubble: Bubble):
        bubble.alive = False
        self._total_pops += 1
        self._pop_particles.append((bubble.x, bubble.y, 0.6))
        self._coins_display.append((bubble.x, bubble.y - 20, 1.2))

        # Water the nearest unwatered flower
        unwatered = [f for f in self.flowers if not f.watered]
        if unwatered:
            nearest = min(unwatered, key=lambda f: abs(f.x - bubble.x))
            nearest.water()

        self.coins_earned += 2
        self.session.score += 2

        if self._total_pops >= 20:
            self.session.unlock_achievement("bubble_master")

    def _complete(self):
        self.completed = True
        self.session.update_high_score(self.game_key, self.session.score)
        self.session.record_play_today()

    def draw(self, surface: pygame.Surface):
        self._ensure_assets()

        # Sky background
        surface.fill((135, 206, 235))

        # Ground
        ground_y = int(self.screen_h * 0.88)
        pygame.draw.rect(surface, (100, 160, 60),
                         (0, ground_y, self.screen_w,
                          self.screen_h - ground_y))

        # Flowers
        for flower in self.flowers:
            flower.draw(surface)

        # Bubbles
        for bubble in self.bubbles:
            bubble.draw(surface)

        # Pop particles
        for x, y, t in self._pop_particles:
            alpha = int(255 * (t / 0.6))
            for i in range(8):
                angle = i * math.pi / 4
                px = int(x + math.cos(angle) * (1.0 - t / 0.6) * 30)
                py = int(y + math.sin(angle) * (1.0 - t / 0.6) * 30)
                pygame.draw.circle(surface, (255, 255, 200), (px, py), 3)

        # Coin pop display
        for x, y, t in self._coins_display:
            surface.blit(self.coins_img, (int(x - 25), int(y - 25 - (1.2 - t) * 40)))

        # Purse progress bar
        bar_w = 160
        bar_h = 18
        bx    = self.screen_w // 2 - bar_w // 2
        by    = int(self.screen_h * 0.10)
        pygame.draw.rect(surface, (200, 200, 200), (bx, by, bar_w, bar_h), border_radius=9)
        fill = int(bar_w * min(self._purse_hold / self.hold_duration, 1.0))
        if fill > 0:
            pygame.draw.rect(surface, (120, 80, 200),
                             (bx, by, fill, bar_h), border_radius=9)
        font_sm = pygame.font.SysFont(None, 22)
        lbl = font_sm.render("Purse to blow bubble", True, (40, 40, 40))
        surface.blit(lbl, (self.screen_w // 2 - lbl.get_width() // 2, by - 20))

        # Score
        font = pygame.font.SysFont(None, 36)
        sc = font.render(f"Coins: {self.coins_earned}", True, (40, 40, 40))
        surface.blit(sc, (10, 10))

        # Flower progress (X/4 watered)
        n_done = sum(1 for f in self.flowers if f.watered)
        prog = font_sm.render(f"Flowers watered: {n_done}/{N_FLOWERS}", True, (40, 40, 40))
        surface.blit(prog, (self.screen_w - prog.get_width() - 10, 10))

        # Win overlay
        if self.completed:
            overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            overlay.fill((255, 255, 200, 160))
            surface.blit(overlay, (0, 0))
            font_big = pygame.font.SysFont(None, 80)
            msg = font_big.render("Garden Bloomed! 🌸", True, (60, 120, 60))
            surface.blit(msg, (self.screen_w // 2 - msg.get_width() // 2,
                               self.screen_h // 2 - 40))
