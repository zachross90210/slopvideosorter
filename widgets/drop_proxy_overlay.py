from PyQt6 import QtCore, QtGui, QtWidgets
from typing import Optional
from logger import get_logger

logger = get_logger(__name__)


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
        logger.debug(f"[DND] target_widget: {type(self).__name__}")
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            logger.debug("[DND] Proxy.dragEnterEvent: accept")
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        logger.debug(f"[DND] target_widget: {type(self).__name__}")
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        logger.debug(f"[DND] target_widget: {type(self).__name__}")
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
            logger.debug(f"[DND] Proxy.dropEvent: filesDropped -> {len(paths)} files")
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

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        # Drive fullscreen overlay show/hide based on bottom-edge hover
        parent = self.parentWidget()
        if parent is not None and hasattr(parent, "isFullScreen") and parent.isFullScreen():
            try:
                y = event.position().y()
            except Exception:
                y = event.y()
            threshold = parent.height() * 0.90
            if y >= threshold:
                # Call parent's overlay show helper if present
                show_fn = getattr(parent, "_showOverlayTemporarily", None)
                if callable(show_fn):
                    show_fn()
            else:
                overlay = getattr(parent, "_overlay", None)
                if overlay is not None:
                    overlay.hide()
        super().mouseMoveEvent(event)
