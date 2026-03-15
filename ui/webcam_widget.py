"""
Renders the live webcam frame into a pygame Surface and blits it to a corner.
"""

import cv2
import numpy as np
import pygame


class WebcamWidget:
    def __init__(self, dest_rect: pygame.Rect):
        """
        dest_rect: where to blit on the main surface (e.g. bottom-right corner).
        """
        self.dest_rect = dest_rect
        self._surface  = pygame.Surface((dest_rect.w, dest_rect.h))
        self._border_color = (80, 200, 120)

    def update(self, bgr_frame: np.ndarray):
        """Convert latest BGR frame to pygame Surface."""
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (self.dest_rect.w, self.dest_rect.h))
        # pygame expects (W, H, 3) with axis order W, H
        # numpy array from cv2 is (H, W, 3) — need to transpose
        pygame_arr = resized.swapaxes(0, 1)
        pygame.surfarray.blit_array(self._surface, pygame_arr)

    def draw(self, surface: pygame.Surface):
        surface.blit(self._surface, self.dest_rect.topleft)
        pygame.draw.rect(surface, self._border_color, self.dest_rect, 3,
                         border_radius=4)
