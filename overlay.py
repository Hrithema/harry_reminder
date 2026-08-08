"""
The transparent, click-through desktop overlay that flies the sprite across
the screen and (optionally) shows a speech-bubble reminder.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QObject, Signal
from PySide6.QtGui import QPixmap, QScreen
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QGraphicsOpacityEffect

import config


class ReminderOverlay(QWidget):
    """
    A single-shot overlay: construct it, call show_reminder(), and it tears
    itself down automatically once the animation sequence finishes.
    """

    finished = Signal()

    def __init__(self, message: str, screen: QScreen | None = None):
        super().__init__()
        self.message = message
        self.screen_obj = screen or QApplication.primaryScreen()
        self._frames: list[QPixmap] = []
        self._frame_index = 0

        self._setup_window()
        self._setup_sprite_label()
        self._setup_speech_bubble()
        self._load_frames()

        self._frame_timer = QTimer(self)
        self._frame_timer.timeout.connect(self._advance_frame)

        self._fly_anim: QPropertyAnimation | None = None

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #
    def _setup_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # keeps it off the taskbar
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        if config.CLICK_THROUGH:
            self.setAttribute(Qt.WA_TransparentForMouseEvents)

        geo = self.screen_obj.geometry()
        self.setGeometry(geo)  # cover the full screen; sprite moves within it

    def _setup_sprite_label(self):
        self.sprite_label = QLabel(self)
        w, h = config.SPRITE_SIZE
        self.sprite_label.setFixedSize(w, h)

    def _setup_speech_bubble(self):
        self.bubble_label = QLabel(self)
        self.bubble_label.setWordWrap(True)
        self.bubble_label.setMaximumWidth(config.BUBBLE_MAX_WIDTH)
        self.bubble_label.setText(self.message)
        self.bubble_label.setStyleSheet(
            f"""
            background-color: rgba(255, 255, 255, 235);
            border: 2px solid rgba(40, 40, 40, 220);
            border-radius: 10px;
            padding: 8px 12px;
            font-family: '{config.BUBBLE_FONT_FAMILY}';
            font-size: {config.BUBBLE_FONT_SIZE}px;
            color: #1a1a1a;
            """
        )
        self.bubble_label.adjustSize()
        self.bubble_label.hide()

        self._bubble_opacity = QGraphicsOpacityEffect(self.bubble_label)
        self.bubble_label.setGraphicsEffect(self._bubble_opacity)
        self._bubble_opacity.setOpacity(0.0)

    def _load_frames(self):
        for name in config.FRAME_FILENAMES:
            path = config.FRAMES_DIR / name
            pix = QPixmap(str(path))
            if pix.isNull():
                continue
            pix = pix.scaled(
                *config.SPRITE_SIZE,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self._frames.append(pix)

        if self._frames:
            self.sprite_label.setPixmap(self._frames[0])

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #
    def show_reminder(self):
        self.show()
        self._frame_timer.start(config.FRAME_INTERVAL_MS)
        self._fly_in()

    # ------------------------------------------------------------------ #
    # Animation stages
    # ------------------------------------------------------------------ #
    def _hover_point(self) -> tuple[QPoint, QPoint]:
        """Returns (start, hover) positions for the sprite based on entry side."""
        geo = self.geometry()
        w, h = config.SPRITE_SIZE
        hover_y = int(geo.height() * config.HOVER_Y_FRACTION) - h // 2

        if config.ENTRY_SIDE == "left":
            start = QPoint(-w, hover_y)
            hover = QPoint(int(geo.width() * 0.25), hover_y)
        else:
            start = QPoint(geo.width(), hover_y)
            hover = QPoint(int(geo.width() * 0.75) - w, hover_y)

        return start, hover

    def _offscreen_exit_point(self) -> QPoint:
        geo = self.geometry()
        _, hover = self._hover_point()
        if config.ENTRY_SIDE == "left":
            return QPoint(geo.width() + config.SPRITE_SIZE[0], hover.y())
        return QPoint(-config.SPRITE_SIZE[0], hover.y())

    def _animate_sprite(self, start: QPoint, end: QPoint, duration_ms: int, on_finished=None):
        self.sprite_label.move(start)
        anim = QPropertyAnimation(self.sprite_label, b"pos", self)
        anim.setDuration(duration_ms)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        if on_finished:
            anim.finished.connect(on_finished)
        anim.start()
        self._fly_anim = anim  # keep a reference so it isn't garbage collected

    def _fly_in(self):
        start, hover = self._hover_point()
        self._animate_sprite(start, hover, config.FLY_IN_DURATION_MS, on_finished=self._on_arrived)

    def _on_arrived(self):
        if config.SHOW_SPEECH_BUBBLE:
            self._show_bubble()
        QTimer.singleShot(config.HOVER_DURATION_MS, self._fly_out)

    def _show_bubble(self):
        _, hover = self._hover_point()
        bubble_x = hover.x() + (config.SPRITE_SIZE[0] - self.bubble_label.width()) // 2
        bubble_y = hover.y() - self.bubble_label.height() - 12
        self.bubble_label.move(max(bubble_x, 4), max(bubble_y, 4))
        self.bubble_label.show()

        anim = QPropertyAnimation(self._bubble_opacity, b"opacity", self)
        anim.setDuration(config.BUBBLE_FADE_MS)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()
        self._bubble_anim = anim

    def _fly_out(self):
        self.bubble_label.hide()
        _, hover = self._hover_point()
        exit_point = self._offscreen_exit_point()
        self._animate_sprite(hover, exit_point, config.FLY_OUT_DURATION_MS, on_finished=self._on_done)

    def _on_done(self):
        self._frame_timer.stop()
        self.finished.emit()
        self.close()

    # ------------------------------------------------------------------ #
    def _advance_frame(self):
        if not self._frames:
            return
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self.sprite_label.setPixmap(self._frames[self._frame_index])
