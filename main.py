import argparse
import random
import sys

from PySide6.QtWidgets import QApplication

import config
from overlay import ReminderOverlay


def parse_args():
    parser = argparse.ArgumentParser(description="Show an animated desktop reminder.")
    parser.add_argument(
        "--message",
        "-m",
        default=random.choice(config.DEFAULT_MESSAGE),
        help="Reminder text to show in the speech bubble."
    )
    parser.add_argument(
        "--side",
        choices=["left", "right"],
        default=None,
        help="Which side the sprite flies in from (overrides config.py).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.side:
        config.ENTRY_SIDE = args.side

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    overlay = ReminderOverlay(message=args.message)
    overlay.finished.connect(app.quit)
    overlay.show_reminder()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
