"""
HUD — 6 animated muscle-level bars.
Shown as a compact panel in a corner of the play screen.
Each bar corresponds to one FaceMetrics channel.
"""

import os
import pygame
from core.metrics import FaceMetrics

ASSETS = os.path.join(os.path.dirname(__file__), "..", "resources")

BAR_W     = 100
BAR_H     = 12
BAR_GAP   = 20    # vertical spacing between bars
LABEL_W   = 90
PANEL_PAD = 8

# Colors for each channel
CHANNEL_COLORS = [
    (80,  200,  80),   # smile_width   — green
    (80,  140, 220),   # mouth_open    — blue
    (220, 180,  80),   # eyebrow_raise — yellow
    (200,  80, 200),   # lip_purse     — purple
    (220, 120,  80),   # cheek_puff    — orange
    (80,  220, 200),   # nose_wrinkle  — teal
]


class HUD:
    def __init__(self, topleft: tuple):
        """
        topleft: (x, y) position of the HUD panel on screen.
        """
        self.x, self.y = topleft
        self._font = None
        n = len(FaceMetrics.CHANNEL_NAMES)
        self.panel_w = LABEL_W + BAR_W + PANEL_PAD * 3
        self.panel_h = n * (BAR_H + BAR_GAP) + PANEL_PAD * 2

    def _get_font(self):
        if self._font is None:
            self._font = pygame.font.SysFont(None, 20)
        return self._font

    def draw(self, surface: pygame.Surface, metrics: FaceMetrics,
             channel_active=None):
        """
        Draw muscle bars.
        channel_active: optional bool array (len 6); dims bars for inactive channels.
        """
        font = self._get_font()

        # Background panel
        panel = pygame.Surface((self.panel_w, self.panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        surface.blit(panel, (self.x, self.y))

        vals = list(metrics.as_dict().values())   # 6 floats
        labels = FaceMetrics.CHANNEL_LABELS

        for i, (name, label, val, color) in enumerate(
                zip(FaceMetrics.CHANNEL_NAMES, labels, vals, CHANNEL_COLORS)):
            bar_y = self.y + PANEL_PAD + i * (BAR_H + BAR_GAP)
            lbl_x = self.x + PANEL_PAD
            bar_x = self.x + LABEL_W + PANEL_PAD

            # Label
            active = (channel_active is None or channel_active[i])
            text_color = (220, 220, 220) if active else (120, 120, 120)
            lbl_surf = font.render(label, True, text_color)
            surface.blit(lbl_surf, (lbl_x, bar_y))

            # Background bar
            pygame.draw.rect(surface, (60, 60, 60),
                             (bar_x, bar_y, BAR_W, BAR_H), border_radius=4)

            # Fill bar
            fill_w = int(BAR_W * min(max(val, 0.0), 1.0))
            if fill_w > 0:
                bar_color = color if active else (100, 100, 100)
                pygame.draw.rect(surface, bar_color,
                                 (bar_x, bar_y, fill_w, BAR_H), border_radius=4)

            # Threshold tick at 0.35
            tick_x = bar_x + int(BAR_W * 0.35)
            pygame.draw.line(surface, (255, 255, 255),
                             (tick_x, bar_y - 1), (tick_x, bar_y + BAR_H + 1), 1)
