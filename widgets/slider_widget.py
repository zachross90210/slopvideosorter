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
