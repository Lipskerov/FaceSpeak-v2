"""
Play screen — composites webcam corner + HUD + active game.
"""

import pygame
from core.metrics import FaceMetrics
from games.base_game import BaseGame
from ui.hud import HUD
from ui.webcam_widget import WebcamWidget


class ScreenPlay:
    def __init__(self, screen: pygame.Surface, on_win_callback, on_back_callback):
        self.screen       = screen
        self.on_win       = on_win_callback
        self.on_back      = on_back_callback

        self.W = screen.get_width()
        self.H = screen.get_height()

        # Webcam corner: bottom-right, 240×180
        cam_w, cam_h = 240, 180
        self._webcam_widget = WebcamWidget(
            pygame.Rect(self.W - cam_w - 8, self.H - cam_h - 8, cam_w, cam_h))

        # HUD: top-right corner
        self._hud = HUD(topleft=(self.W - 220, 8))

        self._game: BaseGame | None = None
        self._back_btn_rect = pygame.Rect(8, 8, 80, 32)

    def set_game(self, game: BaseGame):
        self._game = game

    def update(self, metrics: FaceMetrics, bgr_frame, dt: float):
        if bgr_frame is not None:
            self._webcam_widget.update(bgr_frame)

        if self._game:
            self._game.update(metrics, dt)
            if self._game.completed:
                self.on_win(self._game)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_back()
        if (event.type == pygame.MOUSEBUTTONDOWN and
                self._back_btn_rect.collidepoint(event.pos)):
            self.on_back()

    def draw(self, metrics: FaceMetrics, channel_active=None):
        # Game draws to full surface
        if self._game:
            self._game.draw(self.screen)
        else:
            self.screen.fill((20, 20, 40))

        # HUD overlay
        self._hud.draw(self.screen, metrics, channel_active)

        # Webcam corner
        self._webcam_widget.draw(self.screen)

        # Back button
        font = pygame.font.SysFont(None, 24)
        pygame.draw.rect(self.screen, (50, 50, 70), self._back_btn_rect,
                         border_radius=6)
        lbl = font.render("◀ Menu", True, (200, 200, 200))
        self.screen.blit(lbl, (self._back_btn_rect.x + 6,
                               self._back_btn_rect.y + 8))
