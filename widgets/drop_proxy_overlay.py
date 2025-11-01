from PyQt6 import QtCore, QtGui, QtWidgets
from typing import Optional


class DropProxyOverlay(QtWidgets.QWidget):
    filesDropped = QtCore.pyqtSignal(list)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        # Do NOT use WA_TransparentForMouseEvents; it suppresses drag events too
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        print(f"[DND] target_widget: {type(self).__name__}")
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            print("[DND] Proxy.dragEnterEvent: accept")
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        print(f"[DND] target_widget: {type(self).__name__}")
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        print(f"[DND] target_widget: {type(self).__name__}")
        md = event.mimeData()
        paths = []
        if md.hasUrls():
            for url in md.urls():
                local = url.toLocalFile()
                if not local:
                    local = QtCore.QUrl(url).toLocalFile()
                if local:
                    paths.append(local)
        if not paths and md.hasText():
            text = md.text().strip()
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                url = QtCore.QUrl.fromUserInput(line)
                local = url.toLocalFile()
                if local:
                    paths.append(local)
        if paths:
            print(f"[DND] Proxy.dropEvent: filesDropped -> {len(paths)} files")
            self.filesDropped.emit(paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    # Forward mouse interactions to the underlying video widget so UX (e.g., double-click fullscreen) remains
    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        parent = self.parentWidget()
        if parent is not None:
            QtWidgets.QApplication.sendEvent(parent, event)
        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        parent = self.parentWidget()
        if parent is not None:
            QtWidgets.QApplication.sendEvent(parent, event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        parent = self.parentWidget()
        if parent is not None:
            QtWidgets.QApplication.sendEvent(parent, event)
        else:
            super().mouseReleaseEvent(event)
