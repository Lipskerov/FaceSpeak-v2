"""
3-step guided calibration wizard.
  Step 0: Neutral face — capture 75 frames (3s @ 25fps)
  Step 1–6: Max activation for each of the 6 channels (2s each)
  Step 7: Validation + save

Returns to PLAY screen when done.
"""

import numpy as np
import pygame
from core.metrics import FaceMetrics
from core.signal_processor import SignalProcessor
from core.session import Session

NEUTRAL_FRAMES  = 75    # 3 seconds
MAX_FRAMES      = 50    # 2 seconds per channel
FONT_COLOR      = (240, 240, 240)

STEP_PROMPTS = [
    ("Neutral Face", "Relax your face completely.\nDo not move any muscles.", (150, 150, 150)),
    ("Smile Wide!", "Smile as wide as you can!", (80, 220, 80)),
    ("Open Mouth!", "Open your mouth wide!", (80, 140, 220)),
    ("Raise Eyebrows!", "Raise your eyebrows as high as possible!", (220, 180, 80)),
    ("Purse Lips!", "Press lips together, make them round like 'O'", (200, 80, 200)),
    ("Puff Cheeks!", "Puff out both cheeks!", (220, 120, 80)),
    ("Wrinkle Nose!", "Wrinkle your nose like smelling something bad!", (80, 220, 200)),
]


class ScreenCalibrate:
    def __init__(self, screen: pygame.Surface, processor: SignalProcessor,
                 session: Session, on_done_callback):
        self.screen    = screen
        self.processor = processor
        self.session   = session
        self.on_done   = on_done_callback

        self.W = screen.get_width()
        self.H = screen.get_height()

        self._reset()

    def _reset(self):
        self._step          = 0   # 0 = neutral; 1–6 = channel max activation
        self._frame_count   = 0
        self._collecting    = False
        self._captured      = []   # list of 6-channel arrays captured in this step

        self._neutral_data: list[np.ndarray] = []   # raw EMA samples during neutral
        self._max_data: list[list] = [[] for _ in range(6)]  # per-channel

        self._done          = False
        self._status_msg    = ""

    def start(self):
        """Call when entering calibration screen."""
        self._reset()
        # Try loading previous calibration
        prev = self.session.load_calibration()
        if prev:
            neutral, max_vals = prev
            self.processor.set_calibration(
                np.array(neutral), np.array(max_vals))

    def update(self, dt: float):
        pass   # collection happens in handle_frame

    def handle_frame(self, landmarks_present: bool):
        """Called each frame after face tracking."""
        if self._done or not landmarks_present:
            return

        raw = self.processor.get_smoothed_raw()   # shape (6,)

        if self._collecting:
            if self._step == 0:
                self._neutral_data.append(raw.copy())
                self._frame_count += 1
                if self._frame_count >= NEUTRAL_FRAMES:
                    self._finish_step()
            else:
                ch = self._step - 1
                self._max_data[ch].append(raw[ch])
                self._frame_count += 1
                if self._frame_count >= MAX_FRAMES:
                    self._finish_step()

    def _finish_step(self):
        self._collecting  = False
        self._frame_count = 0

        if self._step < len(STEP_PROMPTS) - 1:
            self._step += 1
        else:
            self._finalise()

    def _finalise(self):
        """Compute calibration from collected data and save."""
        if not self._neutral_data:
            self._status_msg = "No neutral data collected — try again."
            return

        neutral = np.mean(self._neutral_data, axis=0)
        max_vals = neutral.copy()

        for ch in range(6):
            if self._max_data[ch]:
                max_vals[ch] = np.percentile(self._max_data[ch], 90)

        self.processor.set_calibration(neutral, max_vals)
        self.session.save_calibration(neutral.tolist(), max_vals.tolist())
        self._done = True
        self.on_done()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not self._collecting:
                self._collecting  = True
                self._frame_count = 0
                if self._step == 0:
                    self._neutral_data = []
                else:
                    self._max_data[self._step - 1] = []
            elif event.key == pygame.K_ESCAPE:
                self.on_done()   # skip calibration

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Click anywhere to start collecting for this step
            if not self._collecting:
                self._collecting  = True
                self._frame_count = 0
                if self._step == 0:
                    self._neutral_data = []
                else:
                    self._max_data[self._step - 1] = []

    def draw(self, webcam_surface=None):
        self.screen.fill((20, 20, 40))

        font_title = pygame.font.SysFont(None, 54)
        font_body  = pygame.font.SysFont(None, 34)
        font_sm    = pygame.font.SysFont(None, 26)

        step = min(self._step, len(STEP_PROMPTS) - 1)
        title, body, color = STEP_PROMPTS[step]

        # Step indicator
        total_steps = len(STEP_PROMPTS)
        for i in range(total_steps):
            cx = int(self.W / 2 - (total_steps / 2 - i) * 28)
            dot_color = (80, 200, 80) if i <= step else (80, 80, 80)
            pygame.draw.circle(self.screen, dot_color, (cx, 50), 8)

        # Title
        t = font_title.render(title, True, color)
        self.screen.blit(t, (self.W // 2 - t.get_width() // 2, 80))

        # Body (multi-line)
        y = 160
        for line in body.split("\n"):
            s = font_body.render(line, True, FONT_COLOR)
            self.screen.blit(s, (self.W // 2 - s.get_width() // 2, y))
            y += 40

        # Webcam feed
        if webcam_surface:
            ww, wh = webcam_surface.get_size()
            self.screen.blit(webcam_surface,
                             (self.W // 2 - ww // 2, y + 20))

        # Progress bar for collecting
        bar_y = self.H - 160
        bar_w = 400
        bar_x = self.W // 2 - bar_w // 2

        pygame.draw.rect(self.screen, (80, 80, 80),
                         (bar_x, bar_y, bar_w, 24), border_radius=12)

        if self._collecting:
            target = NEUTRAL_FRAMES if self._step == 0 else MAX_FRAMES
            fill = int(bar_w * min(self._frame_count / target, 1.0))
            pygame.draw.rect(self.screen, color,
                             (bar_x, bar_y, fill, 24), border_radius=12)
            hint = font_sm.render("Recording… hold expression!", True, (220, 220, 100))
        else:
            hint = font_sm.render("Click or press SPACE to start recording", True,
                                  (180, 180, 180))

        self.screen.blit(hint, (self.W // 2 - hint.get_width() // 2, bar_y + 32))

        # Skip hint
        skip = font_sm.render("ESC — skip calibration", True, (100, 100, 100))
        self.screen.blit(skip, (self.W - skip.get_width() - 16, self.H - 30))

        if self._status_msg:
            err = font_body.render(self._status_msg, True, (220, 80, 80))
            self.screen.blit(err, (self.W // 2 - err.get_width() // 2, self.H - 60))
