"""
Slop Video Sorter: Video widget with drag-and-drop support and fullscreen overlay.

Copyright (C) 2025 zachross90210 <zachross90210@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from PyQt6 import QtCore, QtGui, QtWidgets, QtMultimedia, QtMultimediaWidgets
from typing import Optional
from widgets.drop_proxy_overlay import DropProxyOverlay
from widgets.slider_widget import SeekSlider
from logger import get_logger

logger = get_logger(__name__)


class DroppableVideoWidget(QtMultimediaWidgets.QVideoWidget):
    filesDropped = QtCore.pyqtSignal(list)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        # Drag-and-drop proxy overlay to reliably catch drops even if the
        # underlying QVideoWidget is a native window that ignores DnD.
        self._dropProxy = DropProxyOverlay(self)
        self._dropProxy.filesDropped.connect(self.filesDropped)
        self._dropProxy.raise_()

        # Fullscreen overlay controls (shown on hover)
        self._player: Optional[QtMultimedia.QMediaPlayer] = None
        # Use a top-level, frameless, translucent window so it can appear over the native video surface
        self._overlay = QtWidgets.QWidget(None)
        self._overlay.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.Tool
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self._overlay.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._overlay.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self._overlay.setStyleSheet(
            """
            background-color: rgba(0, 0, 0, 130);
            color: white;
            """
        )
        self._overlay.hide()

        self._overlayLayout = QtWidgets.QHBoxLayout(self._overlay)
        self._overlayLayout.setContentsMargins(10, 6, 10, 6)
        self._overlayLayout.setSpacing(8)

        self._fsLabelCurrent = QtWidgets.QLabel("00:00", self._overlay)
        self._fsSlider = SeekSlider(QtCore.Qt.Orientation.Horizontal)
        self._fsSlider.setRange(0, 0)
        self._fsSlider.setSingleStep(1000)
        self._fsLabelDuration = QtWidgets.QLabel("00:00", self._overlay)
        # Light slider styling for dark overlay
        self._fsSlider.setStyleSheet(
            """
            QSlider::groove:horizontal { height: 4px; background: rgba(255,255,255,0.25); border-radius: 2px; }
            QSlider::handle:horizontal { width: 12px; height: 12px; margin: -5px 0; border-radius: 6px; background: #2F80ED; }
            QSlider::sub-page:horizontal { background: rgba(47,128,237,0.9); border-radius: 2px; }
            """
        )

        self._overlayLayout.addWidget(self._fsLabelCurrent)
        self._overlayLayout.addWidget(self._fsSlider, 1)
        self._overlayLayout.addWidget(self._fsLabelDuration)

        self._hideTimer = QtCore.QTimer(self)
        self._hideTimer.setSingleShot(True)
        self._hideTimer.timeout.connect(self._overlay.hide)
        # Ensure overlay is above the DnD proxy initially
        self._overlay.raise_()

        # Seek interactions
        self._fsSlider.clickedTo.connect(self._on_fs_slider_clicked)
        self._fsSlider.sliderMoved.connect(self._on_fs_slider_moved)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Toggle fullscreen on the video widget itself
            if hasattr(self, "setFullScreen"):
                self.setFullScreen(not self.isFullScreen())
            else:
                # Fallback for environments without setFullScreen
                if self.isFullScreen():
                    self.showNormal()
                else:
                    self.showFullScreen()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Escape and self.isFullScreen():
            # Exit fullscreen on ESC
            if hasattr(self, "setFullScreen"):
                self.setFullScreen(False)
            else:
                self.showNormal()
            # Hide overlay when leaving fullscreen
            self._overlay.hide()
            event.accept()
            return
        super().keyPressEvent(event)

    # def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
    #     # In fullscreen, only show overlay when cursor is in the bottom 2% area
    #     if self.isFullScreen():
    #         try:
    #             y = event.position().y()
    #         except Exception:
    #             y = event.y()
    #         threshold = self.height() * 0.98

    #         print(f"[FULLSCREEN] y: {y}, threshold: {threshold}")
    #         if y >= threshold:
    #             self._showOverlayTemporarily()
    #         else:
    #             self._overlay.hide()
    #     super().mouseMoveEvent(event)

    def enterEvent(self, event: QtCore.QEvent) -> None:
        # Do not auto-show on enter; rely on bottom-edge hover in fullscreen
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        # Hide sooner when leaving
        if self.isFullScreen():
            self._hideTimer.start(500)
        super().leaveEvent(event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        # Position overlay at bottom inside the video area (in global coords)
        self._updateOverlayGeometry()
        # Ensure the DnD proxy always covers the video area
        self._dropProxy.setGeometry(0, 0, self.width(), self.height())
        # Keep overlay on top (it's a separate window)

    def attachMediaPlayer(self, player: QtMultimedia.QMediaPlayer) -> None:
        # Connect to media player for syncing timeline in fullscreen overlay
        self._player = player
        player.positionChanged.connect(self._on_player_position_changed)
        player.durationChanged.connect(self._on_player_duration_changed)

    def _on_player_duration_changed(self, duration_ms: int) -> None:
        self._fsSlider.setRange(0, int(duration_ms))
        self._fsLabelDuration.setText(self._format_msec(duration_ms))

    def _on_player_position_changed(self, position_ms: int) -> None:
        self._fsSlider.setValue(int(position_ms))
        self._fsLabelCurrent.setText(self._format_msec(position_ms))

    def _on_fs_slider_clicked(self, value: int) -> None:
        if self._player is not None:
            self._player.setPosition(int(value))

    def _on_fs_slider_moved(self, value: int) -> None:
        self._fsLabelCurrent.setText(self._format_msec(int(value)))

    def _showOverlayTemporarily(self) -> None:
        logger.debug("[FULLSCREEN] _showOverlayTemporarily")
        self._updateOverlayGeometry()
        self._overlay.show()
        self._hideTimer.start(1500)

    def _updateOverlayGeometry(self) -> None:
        if not self.isVisible():
            return
        # Calculate overlay rect relative to screen
        h = 44
        margin_side = 10
        # Place a bit lower (closer to the bottom edge) than before
        margin_bottom = 2
        top_left_local = QtCore.QPoint(margin_side, self.height() - h - margin_bottom)
        top_left_global = self.mapToGlobal(top_left_local)
        width = max(0, self.width() - 2 * margin_side)
        self._overlay.setGeometry(top_left_global.x(), top_left_global.y(), width, h)

    def _format_msec(self, msec: int) -> str:
        total_seconds = max(0, int(msec // 1000))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
