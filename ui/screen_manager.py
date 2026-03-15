"""
State machine: MENU → CALIBRATE → PLAY → WIN → MENU
"""

from enum import Enum, auto

import pygame
from core.face_tracker import FaceTracker
from core.signal_processor import SignalProcessor
from core.metrics import FaceMetrics
from core.session import Session
from games.game_journey import GameJourney
from games.game_bubbles import GameBubbles
from ui.screen_menu import ScreenMenu
from ui.screen_calibrate import ScreenCalibrate
from ui.screen_play import ScreenPlay
from ui.screen_win import ScreenWin


class State(Enum):
    MENU      = auto()
    CALIBRATE = auto()
    PLAY      = auto()
    WIN       = auto()


class ScreenManager:
    def __init__(self, screen: pygame.Surface):
        self.screen    = screen
        self.W         = screen.get_width()
        self.H         = screen.get_height()

        self.tracker   = FaceTracker()
        self.processor = SignalProcessor()
        self.session   = Session()
        self.metrics   = FaceMetrics()
        self._bgr_frame = None

        # Screens
        self._menu = ScreenMenu(
            screen, self.session,
            on_select_callback  = self._on_game_selected,
            on_calibrate_callback = self._go_calibrate,
        )
        self._calibrate = ScreenCalibrate(
            screen, self.processor, self.session,
            on_done_callback = self._on_calibrate_done,
        )
        self._play = ScreenPlay(
            screen,
            on_win_callback  = self._on_win,
            on_back_callback = self._go_menu,
        )
        self._win = ScreenWin(
            screen, self.session,
            on_menu_callback   = self._go_menu,
            on_replay_callback = self._replay,
        )

        self._state       = State.MENU
        self._active_game = None
        self._active_game_cfg = None

        # Try loading saved calibration
        prev = self.session.load_calibration()
        if prev:
            import numpy as np
            self.processor.set_calibration(np.array(prev[0]), np.array(prev[1]))

    # ------------------------------------------------------------------
    # Callbacks from screens
    # ------------------------------------------------------------------
    def _on_game_selected(self, key, label, game, color, sub, **kwargs):
        self._active_game_cfg = {"game": game, **kwargs}
        self._launch_game()
        self._state = State.PLAY

    def _launch_game(self):
        cfg = self._active_game_cfg
        if cfg["game"] == "journey":
            g = GameJourney(self.W, self.H, self.session, level=cfg.get("level", 1))
        else:
            g = GameBubbles(self.W, self.H, self.session,
                            difficulty=cfg.get("difficulty", "easy"))
        g.reset()
        self._active_game = g
        self._play.set_game(g)

    def _go_calibrate(self):
        self._calibrate.start()
        self._state = State.CALIBRATE

    def _on_calibrate_done(self):
        self._state = State.MENU

    def _on_win(self, game):
        self._win.enter(game)
        self._state = State.WIN

    def _go_menu(self):
        self._state = State.MENU

    def _replay(self):
        if self._active_game_cfg:
            self._launch_game()
            self._state = State.PLAY

    # ------------------------------------------------------------------
    # Per-frame pipeline: camera → tracking → update → draw
    # ------------------------------------------------------------------
    def process_camera(self, bgr_frame):
        """Call each frame with the raw BGR frame from cv2."""
        self._bgr_frame = bgr_frame
        pts = self.tracker.process(bgr_frame)

        if pts is not None:
            self.metrics = self.processor.process(pts)
            # Achievement: big opener
            if self.metrics.mouth_open > 0.8:
                self._mouth_open_timer = getattr(self, "_mouth_open_timer", 0.0)
                # tracked in update
            else:
                self._mouth_open_timer = 0.0

            if self._state == State.CALIBRATE:
                self._calibrate.handle_frame(landmarks_present=True)
        else:
            self.metrics = FaceMetrics()
            if self._state == State.CALIBRATE:
                self._calibrate.handle_frame(landmarks_present=False)

    def update(self, dt: float):
        # Big opener achievement tracking
        if self.metrics.mouth_open > 0.8:
            self._mouth_open_timer = getattr(self, "_mouth_open_timer", 0.0) + dt
            if self._mouth_open_timer >= 2.0:
                self.session.unlock_achievement("big_opener")
                self._mouth_open_timer = 0.0
        else:
            self._mouth_open_timer = 0.0

        if self._state == State.MENU:
            self._menu.update(dt)
        elif self._state == State.CALIBRATE:
            self._calibrate.update(dt)
        elif self._state == State.PLAY:
            self._play.update(self.metrics, self._bgr_frame, dt)
        elif self._state == State.WIN:
            self._win.update(dt)

    def handle_event(self, event: pygame.event.Event):
        if self._state == State.MENU:
            self._menu.handle_event(event)
        elif self._state == State.CALIBRATE:
            self._calibrate.handle_event(event)
        elif self._state == State.PLAY:
            self._play.handle_event(event)
        elif self._state == State.WIN:
            self._win.handle_event(event)

    def draw(self):
        if self._state == State.MENU:
            self._menu.draw()
        elif self._state == State.CALIBRATE:
            # Pass small webcam surface to calibrate screen
            cam_surf = None
            if self._bgr_frame is not None:
                import cv2
                import numpy as np
                rgb = cv2.cvtColor(self._bgr_frame, cv2.COLOR_BGR2RGB)
                small = cv2.resize(rgb, (320, 240))
                cam_surf = pygame.Surface((320, 240))
                pygame.surfarray.blit_array(cam_surf, small.swapaxes(0, 1))
            self._calibrate.draw(webcam_surface=cam_surf)
        elif self._state == State.PLAY:
            self._play.draw(self.metrics, self.processor.channel_active)
        elif self._state == State.WIN:
            self._win.draw()
