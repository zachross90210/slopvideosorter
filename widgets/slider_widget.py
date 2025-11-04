"""
Slop Video Sorter: Custom slider widgets for seeking and volume control.

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
from PyQt6 import QtCore, QtGui, QtWidgets


class SeekSlider(QtWidgets.QSlider):
    clickedTo = QtCore.pyqtSignal(int)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # Map click to slider value (simple proportional mapping)
            if self.orientation() == QtCore.Qt.Orientation.Horizontal:
                ratio = max(0.0, min(1.0, event.position().x() / max(1, self.width())))
            else:
                ratio = 1.0 - max(0.0, min(1.0, event.position().y() / max(1, self.height())))
            value = self.minimum() + int(ratio * (self.maximum() - self.minimum()))
            self.setValue(value)
            self.clickedTo.emit(value)
            event.accept()
            return
        super().mousePressEvent(event)


class VolumeSlider(SeekSlider):
    """Horizontal volume slider with wheel support (0-100)."""

    def __init__(self, orientation: QtCore.Qt.Orientation = QtCore.Qt.Orientation.Horizontal, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(orientation, parent)
        self.setRange(0, 100)
        self.setSingleStep(2)
        self.setMouseTracking(True)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        # Adjust by step per wheel notch
        delta = event.angleDelta().y()
        step = self.singleStep() or 1
        if delta > 0:
            self.setValue(min(100, self.value() + step))
        elif delta < 0:
            self.setValue(max(0, self.value() - step))
        event.accept()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        # While left button is held, scrub volume based on cursor position
        if event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            try:
                x = event.position().x()
                y = event.position().y()
            except Exception:
                x = event.x()
                y = event.y()
            if self.orientation() == QtCore.Qt.Orientation.Horizontal:
                ratio = max(0.0, min(1.0, x / max(1, self.width())))
            else:
                ratio = 1.0 - max(0.0, min(1.0, y / max(1, self.height())))
            value = self.minimum() + int(ratio * (self.maximum() - self.minimum()))
            self.setValue(value)
            event.accept()
            return
        super().mouseMoveEvent(event)
