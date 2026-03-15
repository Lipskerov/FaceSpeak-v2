"""
Main menu: game picker, level selector, achievement badges.
"""

import pygame
from core.session import Session, ACHIEVEMENTS

FONT_COLOR   = (240, 240, 240)
ACCENT_COLOR = (100, 180, 255)
BTN_COLOR    = (50, 100, 180)
BTN_HOVER    = (80, 140, 220)
BTN_TEXT     = (255, 255, 255)

GAMES = [
    {"key": "journey_1", "label": "Journey to the Star",  "sub": "Level 1 — Walk & Smile",
     "game": "journey", "level": 1, "color": (60, 160, 80)},
    {"key": "journey_2", "label": "Journey to the Star",  "sub": "Level 2 — Over the Hill",
     "game": "journey", "level": 2, "color": (80, 140, 60)},
    {"key": "journey_3", "label": "Journey to the Star",  "sub": "Level 3 — Full Challenge",
     "game": "journey", "level": 3, "color": (100, 120, 40)},
    {"key": "bubbles_e", "label": "Bubble Garden",        "sub": "Easy (1.5s hold)",
     "game": "bubbles", "difficulty": "easy",   "color": (80, 100, 200)},
    {"key": "bubbles_m", "label": "Bubble Garden",        "sub": "Medium (1s hold)",
     "game": "bubbles", "difficulty": "medium", "color": (100, 80, 200)},
    {"key": "bubbles_h", "label": "Bubble Garden",        "sub": "Hard (0.7s hold)",
     "game": "bubbles", "difficulty": "hard",   "color": (140, 60, 200)},
]


class Button:
    def __init__(self, rect: pygame.Rect, label: str, sublabel: str = "",
                 color=BTN_COLOR):
        self.rect     = rect
        self.label    = label
        self.sublabel = sublabel
        self.color    = color
        self.hovered  = False

    def draw(self, surface: pygame.Surface):
        c = BTN_HOVER if self.hovered else self.color
        pygame.draw.rect(surface, c, self.rect, border_radius=10)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=10)

        font    = pygame.font.SysFont(None, 28)
        font_sm = pygame.font.SysFont(None, 22)

        lbl = font.render(self.label, True, BTN_TEXT)
        surface.blit(lbl, (self.rect.x + 12, self.rect.y + 10))

        if self.sublabel:
            sub = font_sm.render(self.sublabel, True, (200, 200, 200))
            surface.blit(sub, (self.rect.x + 12, self.rect.y + 34))

    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, event: pygame.event.Event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and self.rect.collidepoint(event.pos))


class ScreenMenu:
    def __init__(self, screen: pygame.Surface, session: Session,
                 on_select_callback, on_calibrate_callback):
        self.screen       = screen
        self.session      = session
        self.on_select    = on_select_callback   # callback(game_key, game_name, **kwargs)
        self.on_calibrate = on_calibrate_callback

        self.W = screen.get_width()
        self.H = screen.get_height()

        self._build_buttons()

    def _build_buttons(self):
        self._game_buttons: list[tuple] = []  # (Button, game_config)
        cols = 2
        btn_w = 260
        btn_h = 60
        gap_x = 30
        gap_y = 14

        total_w = cols * btn_w + (cols - 1) * gap_x
        start_x = (self.W - total_w) // 2
        start_y = 160

        for i, cfg in enumerate(GAMES):
            col = i % cols
            row = i // cols
            x = start_x + col * (btn_w + gap_x)
            y = start_y + row * (btn_h + gap_y)
            btn = Button(pygame.Rect(x, y, btn_w, btn_h),
                         cfg["label"], cfg["sub"], cfg["color"])
            self._game_buttons.append((btn, cfg))

        # Calibrate button
        cal_y = start_y + len(GAMES) // cols * (btn_h + gap_y) + 30
        self._calib_btn = Button(
            pygame.Rect(self.W // 2 - 140, cal_y, 280, 50),
            "⚙  Calibrate Face",
            color=(60, 60, 80))

    def handle_event(self, event: pygame.event.Event):
        for btn, cfg in self._game_buttons:
            if btn.is_clicked(event):
                self.on_select(**cfg)
                return

        if self._calib_btn.is_clicked(event):
            self.on_calibrate()

    def update(self, dt: float):
        pos = pygame.mouse.get_pos()
        for btn, _ in self._game_buttons:
            btn.check_hover(pos)
        self._calib_btn.check_hover(pos)

    def draw(self):
        self.screen.fill((15, 20, 40))

        font_title = pygame.font.SysFont(None, 72)
        font_sub   = pygame.font.SysFont(None, 30)
        font_sm    = pygame.font.SysFont(None, 22)

        # Title
        title = font_title.render("FaceSpeak", True, (100, 200, 255))
        self.screen.blit(title, (self.W // 2 - title.get_width() // 2, 30))

        sub = font_sub.render("Face Muscle Training", True, (160, 160, 200))
        self.screen.blit(sub, (self.W // 2 - sub.get_width() // 2, 100))

        # Game buttons
        for btn, _ in self._game_buttons:
            btn.draw(self.screen)

        # Calibrate button
        self._calib_btn.draw(self.screen)

        # Achievements panel
        ach_y = self.H - 120
        ach_title = font_sm.render("Achievements:", True, (180, 180, 180))
        self.screen.blit(ach_title, (20, ach_y))

        earned = self.session.all_achievements()
        for j, (key, info) in enumerate(ACHIEVEMENTS.items()):
            x = 20 + j * 110
            y = ach_y + 20
            color = (220, 180, 60) if key in earned else (60, 60, 60)
            pygame.draw.rect(self.screen, color,
                             (x, y, 100, 70), border_radius=8)
            pygame.draw.rect(self.screen, (100, 100, 100),
                             (x, y, 100, 70), 1, border_radius=8)
            lbl_lines = info["label"].split(" ")
            for li, line in enumerate(lbl_lines):
                lbl_s = font_sm.render(line, True, (240, 240, 240))
                self.screen.blit(lbl_s, (x + 4, y + 6 + li * 18))

        # High scores
        hs_x = self.W - 200
        hs_title = font_sm.render("High Scores:", True, (180, 180, 180))
        self.screen.blit(hs_title, (hs_x, ach_y))
        for j, cfg in enumerate(GAMES[:4]):
            hs = self.session.high_score(cfg["key"])
            if hs > 0:
                sc_s = font_sm.render(f"{cfg['sub'][:18]}: {hs}", True, (200, 200, 200))
                self.screen.blit(sc_s, (hs_x, ach_y + 20 + j * 20))
