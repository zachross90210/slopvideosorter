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
