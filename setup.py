"""
py2app setup — builds dist/FaceSpeak.app
Run: python setup.py py2app
"""

from setuptools import setup

APP = ["main.py"]
DATA_FILES = [
    ("resources", [
        "resources/bg_final_s.png",
        "resources/bg_final.png",
        "resources/boy_start.png",
        "resources/boy_final.png",
        "resources/balloon.png",
        "resources/win.png",
        "resources/coins.png",
        "resources/muscles.png",
    ]),
    ("data", []),
]
OPTIONS = {
    "argv_emulation": False,   # MUST be False on M1 (Carbon is x86-only)
    "packages": [
        "mediapipe",
        "cv2",
        "pygame",
        "numpy",
    ],
    "includes": [
        "core",
        "games",
        "ui",
    ],
    "plist": {
        "CFBundleName": "FaceSpeak",
        "CFBundleDisplayName": "FaceSpeak",
        "CFBundleVersion": "2.0.0",
        "NSCameraUsageDescription":
            "FaceSpeak needs camera access for face muscle training.",
        "NSHighResolutionCapable": True,
        "LSUIElement": False,
    },
    "excludes": ["matplotlib", "wx", "tkinter", "PyQt5", "PyQt6"],
    "iconfile": None,   # add .icns here when available
}

setup(
    app=APP,
    name="FaceSpeak",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
