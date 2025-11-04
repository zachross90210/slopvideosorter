"""
Slop Video Sorter: Playlist widget with drag-and-drop and keyboard shortcuts support.

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
from PyQt6 import QtCore, QtGui, QtWidgets, QtMultimedia
from typing import Optional


class PlaylistWidget(QtWidgets.QListWidget):
    deleteSelectedRequested = QtCore.pyqtSignal()
    externalFilesDropped = QtCore.pyqtSignal(list)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(False)
        # Default: do not allow drag-drop unless Ctrl is held
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.NoDragDrop)
        self.setDefaultDropAction(QtCore.Qt.DropAction.MoveAction)
        self.setAcceptDrops(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)

        # Visual style: white items; blue selection
        self.setStyleSheet(
            """
            QListWidget::item {
                background: white;
                color: black;
                padding: 4px 6px;
            }
            QListWidget::item:selected {
                background: #2F80ED; /* blue */
                color: white;
            }
            """
        )

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        # Enable internal move only while Ctrl is held
        if event.key() in (QtCore.Qt.Key.Key_Control,):
            self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)

        # Shift + Delete triggers deletion of selected items and underlying files
        if event.key() == QtCore.Qt.Key.Key_Delete and event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier:
            event.accept()
            self.deleteSelectedRequested.emit()
            return

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        # Disable drag-drop once Ctrl is released
        if event.key() in (QtCore.Qt.Key.Key_Control,):
            self.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.NoDragDrop)
        super().keyReleaseEvent(event)

    def startDrag(self, supportedActions: QtCore.Qt.DropAction) -> None:
        # Only start drag if Ctrl is held (safety)
        if not (QtWidgets.QApplication.keyboardModifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            return
        super().startDrag(supportedActions)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        # Ensure drops are accepted even when playlist is empty
        md = event.mimeData()
        if md.hasUrls():
            event.acceptProposedAction()
            # Explicitly ensure accept drops is still enabled (might be reset when playlist becomes empty)
            if not self.acceptDrops():
                self.setAcceptDrops(True)
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        md = event.mimeData()
        if md.hasUrls():
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        md = event.mimeData()
        if md.hasUrls():
            paths = []
            for url in md.urls():
                local = url.toLocalFile()
                if local:
                    paths.append(local)
            if paths:
                self.externalFilesDropped.emit(paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)
