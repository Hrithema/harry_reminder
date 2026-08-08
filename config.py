"""
Central configuration for the desktop reminder app.
Edit these values (or override via CLI args) to change behavior.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FRAMES_DIR = ASSETS_DIR / "frames"

# --- Animation ---
SPRITE_SIZE = (140, 140)          # width, height in px of each frame
FRAME_FILENAMES = [                # sequential PNG frames, played in a loop
    "frame_1.png",
    "frame_2.png",
    "frame_3.png",
    "frame_4.png",
]
FRAME_INTERVAL_MS = 90              # how fast frames cycle (flap speed)

FLY_IN_DURATION_MS = 1400           # time to fly from edge to hover point
HOVER_DURATION_MS = 3500            # time spent hovering while message shows
FLY_OUT_DURATION_MS = 1200          # time to fly off screen

# Vertical position of the hover point, as a fraction of screen height
HOVER_Y_FRACTION = 0.75

# Entry side: "left" or "right"
ENTRY_SIDE = "left"

# --- Speech bubble ---
SHOW_SPEECH_BUBBLE = True
BUBBLE_FONT_FAMILY = "Segoe UI"
BUBBLE_FONT_SIZE = 13
BUBBLE_MAX_WIDTH = 260
BUBBLE_FADE_MS = 250

# --- Window behavior ---
CLICK_THROUGH = True               # let clicks pass through to desktop
ALWAYS_ON_TOP = True

# --- Default reminder (used if none passed on the command line) ---
DEFAULT_MESSAGE = "Hey! Drink some water."
