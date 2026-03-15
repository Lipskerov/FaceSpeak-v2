"""
Abstract base class for all FaceSpeak mini-games.
"""

from abc import ABC, abstractmethod
import pygame
from core.metrics import FaceMetrics
from core.session import Session


class BaseGame(ABC):
    def __init__(self, screen_w: int, screen_h: int, session: Session):
        self.screen_w  = screen_w
        self.screen_h  = screen_h
        self.session   = session
        self.completed = False
        self.coins_earned = 0

    @abstractmethod
    def update(self, metrics: FaceMetrics, dt: float):
        """Called every frame with current face metrics. dt = seconds since last frame."""

    @abstractmethod
    def draw(self, surface: pygame.Surface):
        """Draw game content onto the given surface."""

    @abstractmethod
    def reset(self):
        """Reset game to initial state."""

    @property
    @abstractmethod
    def game_key(self) -> str:
        """Unique string key used for high scores ('journey', 'bubbles', …)."""
