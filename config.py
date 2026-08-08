"""
Central configuration for the desktop reminder app.
Edit these values (or override via CLI args) to change behavior.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
FRAMES_DIR = ASSETS_DIR / "frames"

# --- Animation ---
SPRITE_SIZE = (140, 140)          
FRAME_FILENAMES = [               
    "frame_1.png",
    "frame_2.png",
    "frame_3.png",
    "frame_4.png",
]
FRAME_INTERVAL_MS = 90            

FLY_IN_DURATION_MS = 1400         
HOVER_DURATION_MS = 3500          
FLY_OUT_DURATION_MS = 1200        


HOVER_Y_FRACTION = 0.75

ENTRY_SIDE = "left"

SHOW_SPEECH_BUBBLE = True
BUBBLE_FONT_FAMILY = "Segoe UI"
BUBBLE_FONT_SIZE = 13
BUBBLE_MAX_WIDTH = 260
BUBBLE_FADE_MS = 250

CLICK_THROUGH = True               
ALWAYS_ON_TOP = True


DEFAULT_MESSAGE = ["Hey, go drink some water!",
                   "Your body is asking for hydration!",
                   "Water break! Go grab a glass.",
                   "Tiny reminder: hydrate yourself!",
                   "Pause. Breathe. Drink some water.",
                   "Your water is waiting for you!",
                   "Hydration check! Have you had water?",
                   "Drink water. Your future self will thank you.",
                   "A little water break never hurt anyone!"]
