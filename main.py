"""
FaceSpeak V2 — main entry point.
Single pygame window, 25fps game loop.
"""

import sys
import cv2
import pygame
from ui.screen_manager import ScreenManager


def find_builtin_camera_index() -> int:
    """
    Use AVFoundation to enumerate cameras and return the index of the
    built-in FaceTime camera, skipping iPhone Continuity Camera devices.
    Falls back to index 0 if pyobjc is unavailable.
    """
    try:
        import AVFoundation
        devices = AVFoundation.AVCaptureDevice.devicesWithMediaType_(
            AVFoundation.AVMediaTypeVideo)
        for i, d in enumerate(devices):
            name = d.localizedName() or ""
            uid  = d.uniqueID() or ""
            # iPhone/iPad Continuity Camera devices contain these strings
            if any(k in name.lower() for k in ("iphone", "ipad", "continuity")):
                continue
            if any(k in uid.lower() for k in ("iphone", "ipad")):
                continue
            print(f"[FaceSpeak] Using camera {i}: {name}")
            return i
        # All cameras scanned — fall back to last one found (likely built-in)
        if devices:
            print(f"[FaceSpeak] Falling back to camera 0: {devices[0].localizedName()}")
        return 0
    except Exception:
        return 0

WINDOW_W = 900
WINDOW_H = 650
TARGET_FPS = 25
TITLE = "FaceSpeak — Face Muscle Training"


def main():
    pygame.init()
    pygame.font.init()

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption(TITLE)
    clock  = pygame.time.Clock()

    # Open built-in webcam (skip iPhone Continuity Camera if present)
    cam_index = find_builtin_camera_index()
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print("[FaceSpeak] ERROR: Cannot open webcam.")
        sys.exit(1)

    manager = ScreenManager(screen)

    running = True
    while running:
        dt = clock.tick(TARGET_FPS) / 1000.0   # seconds since last frame

        # --- Camera frame ---
        ret, bgr_frame = cap.read()
        if ret:
            # Mirror horizontally so it feels like a mirror
            bgr_frame = cv2.flip(bgr_frame, 1)
            manager.process_camera(bgr_frame)

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False
            else:
                manager.handle_event(event)

        # --- Update ---
        manager.update(dt)

        # --- Draw ---
        manager.draw()
        pygame.display.flip()

    cap.release()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
