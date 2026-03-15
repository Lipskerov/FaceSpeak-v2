"""
Win / celebration screen — coin shower + achievements earned.
"""

import random
import pygame
from core.session import Session, ACHIEVEMENTS
from games.base_game import BaseGame


class Coin:
    def __init__(self, x: float, screen_h: int):
        self.x  = x
        self.y  = float(random.randint(-100, 0))
        self.vy = random.uniform(100, 260)
        self.vx = random.uniform(-30, 30)
        self.color = random.choice([
            (255, 215, 0), (255, 180, 30), (220, 200, 60)
        ])
        self.radius = random.randint(8, 16)
        self.screen_h = screen_h

    def update(self, dt: float):
        self.vy += 300 * dt   # gravity
        self.y  += self.vy * dt
        self.x  += self.vx * dt

    def draw(self, surface: pygame.Surface):
        if 0 < self.y < self.screen_h + 20:
            pygame.draw.circle(surface, self.color,
                               (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, (255, 250, 200),
                               (int(self.x) - 3, int(self.y) - 3), self.radius // 3)


class ScreenWin:
    def __init__(self, screen: pygame.Surface, session: Session,
                 on_menu_callback, on_replay_callback):
        self.screen     = screen
        self.session    = session
        self.on_menu    = on_menu_callback
        self.on_replay  = on_replay_callback

        self.W = screen.get_width()
        self.H = screen.get_height()

        self._coins: list[Coin] = []
        self._spawn_timer = 0.0
        self._game: BaseGame | None = None
        self._new_achievements: list[str] = []

        self._menu_btn   = pygame.Rect(self.W // 2 - 200, self.H - 80, 180, 50)
        self._replay_btn = pygame.Rect(self.W // 2 + 20,  self.H - 80, 180, 50)

    def enter(self, game: BaseGame):
        self._game = game
        self._new_achievements = list(self.session.new_achievements)
        self.session.new_achievements.clear()
        self._coins = []
        self._spawn_timer = 0.0

    def update(self, dt: float):
        # Spawn coins
        self._spawn_timer += dt
        if self._spawn_timer > 0.04:
            self._spawn_timer = 0.0
            if len(self._coins) < 80:
                self._coins.append(
                    Coin(random.uniform(0, self.W), self.H))

        for c in self._coins:
            c.update(dt)

        # Remove fallen coins
        self._coins = [c for c in self._coins if c.y < self.H + 30]

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self._menu_btn.collidepoint(event.pos):
                self.on_menu()
            elif self._replay_btn.collidepoint(event.pos):
                self.on_replay()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.on_menu()
            if event.key == pygame.K_r:
                self.on_replay()

    def draw(self):
        self.screen.fill((10, 20, 40))

        # Coins
        for c in self._coins:
            c.draw(self.screen)

        # Title
        font_big  = pygame.font.SysFont(None, 90)
        font_med  = pygame.font.SysFont(None, 44)
        font_sm   = pygame.font.SysFont(None, 28)

        title = font_big.render("You Did It! ⭐", True, (255, 215, 0))
        self.screen.blit(title, (self.W // 2 - title.get_width() // 2, 60))

        # Score
        if self._game:
            coins_text = font_med.render(
                f"Coins earned: {self._game.coins_earned}", True, (200, 240, 200))
            self.screen.blit(coins_text,
                             (self.W // 2 - coins_text.get_width() // 2, 165))

        # New achievements
        if self._new_achievements:
            ach_y = 230
            hdr = font_med.render("New Achievements Unlocked!", True, (255, 220, 80))
            self.screen.blit(hdr, (self.W // 2 - hdr.get_width() // 2, ach_y))
            ach_y += 50

            for key in self._new_achievements:
                info = ACHIEVEMENTS.get(key, {})
                label = info.get("label", key)
                desc  = info.get("desc", "")
                badge_rect = pygame.Rect(self.W // 2 - 200, ach_y, 400, 60)
                pygame.draw.rect(self.screen, (80, 60, 20), badge_rect,
                                 border_radius=10)
                pygame.draw.rect(self.screen, (220, 180, 60), badge_rect,
                                 2, border_radius=10)
                lbl = font_med.render(f"🏆 {label}", True, (255, 220, 80))
                self.screen.blit(lbl, (badge_rect.x + 10, badge_rect.y + 6))
                d = font_sm.render(desc, True, (200, 200, 180))
                self.screen.blit(d, (badge_rect.x + 10, badge_rect.y + 36))
                ach_y += 70

        # Buttons
        for rect, label in [(self._menu_btn, "Main Menu"),
                            (self._replay_btn, "Play Again (R)")]:
            pygame.draw.rect(self.screen, (50, 100, 180), rect, border_radius=10)
            pygame.draw.rect(self.screen, (180, 180, 220), rect, 2, border_radius=10)
            lbl = font_med.render(label, True, (255, 255, 255))
            self.screen.blit(lbl, (rect.x + rect.w // 2 - lbl.get_width() // 2,
                                   rect.y + rect.h // 2 - lbl.get_height() // 2))
