"""
Slop Video Sorter: Main window widget for the video player application.

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
import os
from PyQt6 import QtCore, QtGui, QtWidgets, QtMultimedia
from typing import Optional, List
from pathlib import Path
from widgets.playlist_widget import PlaylistWidget
from widgets.video_widget import DroppableVideoWidget
from widgets.slider_widget import SeekSlider, VolumeSlider
from utils import is_video_file, natural_key, find_similar_files, get_saved_directory, unique_dest_path, safe_move_file, safe_delete_file
from logger import get_logger

logger = get_logger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Slop Video Sorter")
        self.resize(1200, 700)
        self.setAcceptDrops(True)
        
        # Set window icon
        icon_path = Path(__file__).parent.parent / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))

        # Media player setup
        self.mediaPlayer = QtMultimedia.QMediaPlayer(self)
        self.audioOutput = QtMultimedia.QAudioOutput(self)
        self.mediaPlayer.setAudioOutput(self.audioOutput)
        self.videoWidget = DroppableVideoWidget(self)
        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.videoWidget.attachMediaPlayer(self.mediaPlayer)

        # Playlist
        self.playlist = PlaylistWidget(self)
        self.playlist.setMinimumWidth(320)
        self.playlist.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.playlist.customContextMenuRequested.connect(self.on_playlist_context_menu)
        self.playlist.deleteSelectedRequested.connect(self.delete_selected_files)
        self.playlist.externalFilesDropped.connect(self.on_playlist_external_files)

        # Controls
        self.openButton = QtWidgets.QPushButton("Open Files…")
        self.openButton.clicked.connect(self.open_files)

        self.playButton = QtWidgets.QPushButton("Play")
        self.playButton.clicked.connect(self.toggle_play_pause)

        self.prevButton = QtWidgets.QPushButton("Prev")
        self.prevButton.clicked.connect(self.play_previous)

        self.nextButton = QtWidgets.QPushButton("Next")
        self.nextButton.clicked.connect(self.play_next)

        # Fancy icons and styles for media controls
        style = self.style()
        self.iconPlay = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay)
        self.iconPause = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause)
        self.iconPrev = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaSkipBackward)
        self.iconNext = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaSkipForward)
        self.iconVolume = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaVolume)
        # Some styles may not provide muted icon; fall back to the same icon
        try:
            self.iconVolumeMuted = style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaVolumeMuted)  # type: ignore[attr-defined]
        except Exception:
            self.iconVolumeMuted = self.iconVolume

        # Icon-only minimalist buttons (same size, Play ~5% larger)
        self.playButton.setText("")
        self.prevButton.setText("")
        self.nextButton.setText("")
        self.playButton.setIcon(self.iconPlay)
        self.prevButton.setIcon(self.iconPrev)
        self.nextButton.setIcon(self.iconNext)
        base_btn = 32
        play_btn = int(base_btn * 1.05)
        self.prevButton.setFixedSize(base_btn, base_btn)
        self.nextButton.setFixedSize(base_btn, base_btn)
        self.playButton.setFixedSize(play_btn, play_btn)
        self.prevButton.setIconSize(QtCore.QSize(18, 18))
        self.nextButton.setIconSize(QtCore.QSize(18, 18))
        self.playButton.setIconSize(QtCore.QSize(19, 19))
        self.playButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.prevButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.nextButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))

        # Save button (green, next to Next button)
        self.saveButton = QtWidgets.QPushButton("✓")
        self.saveButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.saveButton.setFixedSize(base_btn, base_btn)
        self.saveButton.setIconSize(QtCore.QSize(18, 18))
        self.saveButton.setStyleSheet(
            """
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                border-radius: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:pressed { background-color: #1E8449; }
            """
        )
        self.saveButton.clicked.connect(self.save_current_and_play_next)

        minimalStyle = (
            """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
            }
            QPushButton:hover { background-color: rgba(0,0,0,0.06); }
            QPushButton:pressed { background-color: rgba(0,0,0,0.12); }
            """
        )
        self.prevButton.setStyleSheet(minimalStyle)
        self.nextButton.setStyleSheet(minimalStyle)
        # Slightly larger radius for the slightly bigger play button
        self.playButton.setStyleSheet(
            minimalStyle.replace("border-radius: 16px;", f"border-radius: {int(play_btn/2)}px;")
        )

        # Audio controls
        self.muteButton = QtWidgets.QPushButton("")
        self.muteButton.setIcon(self.iconVolume)
        self.muteButton.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.muteButton.setFixedSize(28, 28)
        self.muteButton.setIconSize(QtCore.QSize(18, 18))
        self.muteButton.setStyleSheet(minimalStyle.replace("border-radius: 16px;", "border-radius: 14px;"))
        self.muteButton.clicked.connect(self.toggle_mute)

        self.volumeSlider = VolumeSlider(QtCore.Qt.Orientation.Horizontal)
        self.volumeSlider.setFixedWidth(120)
        self.volumeSlider.setValue(50)
        # Initialize audio output volume to match slider (0.0 - 1.0)
        try:
            self.audioOutput.setVolume(self.volumeSlider.value() / 100.0)
        except Exception:
            pass
        self._lastNonZeroVolume = self.volumeSlider.value()
        self.volumeSlider.valueChanged.connect(self.on_volume_changed)

        # Timeline (progress bar) and time labels
        self.labelCurrentTime = QtWidgets.QLabel("00:00")
        self.positionSlider = SeekSlider(QtCore.Qt.Orientation.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.setSingleStep(1000)  # 1s steps when using arrow keys
        self.labelDuration = QtWidgets.QLabel("00:00")
        self.labelPlaylistCount = QtWidgets.QLabel("0/0")
        self.labelSavePath = QtWidgets.QLabel("")
        self.labelSavePath.setWordWrap(True)
        self.labelSavePath.setStyleSheet("color: gray; font-size: 9pt; padding: 4px;")
        self._isSeeking = False

        self.labelOverrideSave = QtWidgets.QLabel("Override save folder:")
        self.lineEditOverrideSave = QtWidgets.QLineEdit(self)
        self.lineEditOverrideSave.setPlaceholderText("Leave empty for default from config")
        self.lineEditOverrideSave.setClearButtonEnabled(True)
        self.lineEditOverrideSave.setMinimumWidth(280)
        self.lineEditOverrideSave.textChanged.connect(self._update_save_path)

        self.checkDoNotPlayNext = QtWidgets.QCheckBox("Do not play next file")
        self.checkDoNotPlayNext.setToolTip("When checked, playback stops at the end of each file instead of advancing to the next.")

        # Layout
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        mainLayout = QtWidgets.QVBoxLayout(central)

        contentLayout = QtWidgets.QHBoxLayout()
        # Left panel (video only; controls moved to bottom bar to maximize video area)
        leftPanel = QtWidgets.QWidget(self)
        leftLayout = QtWidgets.QVBoxLayout(leftPanel)
        leftLayout.setContentsMargins(0, 0, 0, 0)
        leftLayout.addWidget(self.videoWidget)

        # Timeline row (bottom bar)
        timelineLayout = QtWidgets.QHBoxLayout()
        timelineLayout.addWidget(self.labelCurrentTime)
        timelineLayout.addWidget(self.positionSlider, stretch=1)
        timelineLayout.addWidget(self.labelDuration)
        timelineLayout.addWidget(self.labelPlaylistCount)

        contentLayout.addWidget(leftPanel, stretch=3)
        contentLayout.addWidget(self.playlist, stretch=1)

        # Minimalist media controls row (bottom bar)
        mediaControlsBottom = QtWidgets.QHBoxLayout()
        mediaControlsBottom.addStretch(1)
        mediaControlsBottom.addWidget(self.prevButton)
        mediaControlsBottom.addSpacing(6)
        mediaControlsBottom.addWidget(self.playButton)
        mediaControlsBottom.addSpacing(6)
        mediaControlsBottom.addWidget(self.nextButton)
        mediaControlsBottom.addSpacing(6)
        mediaControlsBottom.addWidget(self.saveButton)
        mediaControlsBottom.addSpacing(12)
        mediaControlsBottom.addWidget(self.muteButton)
        mediaControlsBottom.addSpacing(6)
        mediaControlsBottom.addWidget(self.volumeSlider)
        mediaControlsBottom.addSpacing(16)
        mediaControlsBottom.addWidget(self.checkDoNotPlayNext)
        mediaControlsBottom.addStretch(1)

        mainLayout.addLayout(contentLayout, stretch=1)
        mainLayout.addLayout(timelineLayout)
        overrideRow = QtWidgets.QHBoxLayout()
        overrideRow.addWidget(self.labelOverrideSave)
        overrideRow.addWidget(self.lineEditOverrideSave, stretch=1)
        mainLayout.addLayout(overrideRow)
        mainLayout.addWidget(self.labelSavePath)
        mainLayout.addLayout(mediaControlsBottom)

        # Shortcuts
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+O"), self, activated=self.open_files)
        QtGui.QShortcut(QtGui.QKeySequence("Space"), self, activated=self.toggle_play_pause)

        # Media signals
        self.mediaPlayer.mediaStatusChanged.connect(self.on_media_status_changed)
        self.mediaPlayer.playbackStateChanged.connect(self.on_playback_state_changed)
        self.videoWidget.filesDropped.connect(self.on_video_files_dropped)

        # Position/Duration updates
        self.mediaPlayer.positionChanged.connect(self.on_position_changed)
        self.mediaPlayer.durationChanged.connect(self.on_duration_changed)
        self.positionSlider.sliderPressed.connect(self.on_seek_started)
        self.positionSlider.sliderReleased.connect(self.on_seek_released)
        self.positionSlider.sliderMoved.connect(self.on_slider_moved)
        self.positionSlider.clickedTo.connect(self.on_slider_clicked)

        # Keep icon in sync when playback state changes (already handled); also reflect mute state
        try:
            self.audioOutput.mutedChanged.connect(self._update_mute_icon)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        # Initial update of save path display
        self._update_save_path()

    # ------------------- UI/Actions -------------------
    def open_files(self) -> None:
        dlg = QtWidgets.QFileDialog(self, "Open video files")
        dlg.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFiles)
        dlg.setNameFilters([
            "Video files (*.mp4 *.mkv *.avi *.mov *.webm *.mpg *.mpeg *.m4v *.flv *.wmv)",
            "All files (*)",
        ])
        if dlg.exec():
            files = [Path(p) for p in dlg.selectedFiles()]
            self.add_files(files)

    def on_playlist_context_menu(self, pos: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        addSimilar = menu.addAction("Add similar files in folder")
        saveSelected = menu.addAction("Save this file")
        deleteSelected = menu.addAction("Delete selected (Shift+Del)")
        action = menu.exec(self.playlist.mapToGlobal(pos))
        if action == addSimilar:
            self.add_similar_for_selection()
        elif action == saveSelected:
            self.save_selected_files()
        elif action == deleteSelected:
            self.delete_selected_files()

    def add_files(self, files: List[Path], autoplay_if_stopped: bool = True, source_dir: Optional[Path] = None) -> None:
        added_any = False
        for path in files:
            if not is_video_file(path):
                continue
            if self._has_path_in_playlist(path):
                continue
            item = QtWidgets.QListWidgetItem(path.name)
            # Store absolute path in UserRole
            item.setData(QtCore.Qt.ItemDataRole.UserRole, str(path.resolve()))
            # Store source directory in UserRole + 1 (if provided) for save-to-parent logic
            if source_dir:
                item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, str(source_dir.resolve()))
            # Ensure default white background for unselected state
            item.setBackground(QtGui.QBrush(QtGui.QColor("white")))
            self.playlist.addItem(item)
            added_any = True
        if (
            autoplay_if_stopped
            and added_any
            and self.mediaPlayer.playbackState() == QtMultimedia.QMediaPlayer.PlaybackState.StoppedState
        ):
            # Auto-select first item
            self.play_item_at(0)
        if added_any:
            self._update_playlist_count()

    def on_playlist_external_files(self, path_strs: List[str]) -> None:
        paths = [Path(p) for p in path_strs]
        collected: List[Path] = []
        source_dir: Optional[Path] = None
        # Check if a directory was dropped; use the first directory found
        for p in paths:
            if p.is_dir() and not any(part == "_saved" for part in p.parts):
                source_dir = p
                break
        for p in paths:
            # Skip anything inside a _saved folder
            if any(part == "_saved" for part in p.parts):
                continue
            if p.is_dir():
                try:
                    for child in p.rglob('*'):
                        # Skip files in any _saved subfolder
                        if any(part == "_saved" for part in child.parts):
                            continue
                        if is_video_file(child):
                            collected.append(child)
                except Exception:
                    pass
            elif is_video_file(p):
                collected.append(p)
        if collected:
            collected.sort(key=lambda pa: natural_key(pa.name))
            # Do not autoplay when files are dropped onto the playlist
            # Pass source_dir so save can create _saved in its parent
            self.add_files(collected, autoplay_if_stopped=False, source_dir=source_dir)

    def _has_path_in_playlist(self, path: Path) -> bool:
        abs_str = str(path.resolve())
        for i in range(self.playlist.count()):
            item = self.playlist.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == abs_str:
                return True
        return False

    def on_item_double_clicked(self, item: QtWidgets.QListWidgetItem) -> None:
        row = self.playlist.row(item)
        self.play_item_at(row)

    def current_row(self) -> int:
        # Find row by current media source file path (normalized so Windows path quirks don't break "play next")
        current_url = self.mediaPlayer.source().toLocalFile()
        if not current_url:
            return -1
        # Normalize so Qt's forward-slash paths match Path.resolve() backslashes on Windows
        norm = os.path.normcase(os.path.abspath(current_url))
        for i in range(self.playlist.count()):
            item = self.playlist.item(i)
            p = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if p and os.path.normcase(os.path.abspath(p)) == norm:
                return i
        return -1

    def play_item_at(self, row: int) -> None:
        if row < 0 or row >= self.playlist.count():
            return
        item = self.playlist.item(row)
        path_str = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not path_str:
            return
        url = QtCore.QUrl.fromLocalFile(path_str)
        self.mediaPlayer.setSource(url)
        self.mediaPlayer.play()
        self.playlist.setCurrentRow(row)
        self._highlight_current_in_playlist()

    def play_next(self) -> None:
        row = self.current_row()
        if row == -1:
            if self.playlist.count() > 0:
                self.play_item_at(0)
            return
        next_row = row + 1
        if next_row >= self.playlist.count():
            return
        self.play_item_at(next_row)

    def play_previous(self) -> None:
        row = self.current_row()
        prev_row = max(0, row - 1) if row != -1 else 0
        if self.playlist.count() == 0:
            return
        self.play_item_at(prev_row)

    def toggle_play_pause(self) -> None:
        state = self.mediaPlayer.playbackState()
        if state == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            self.mediaPlayer.pause()
        else:
            if self.mediaPlayer.source().isEmpty():
                # Try to play current selection or first item
                row = self.playlist.currentRow()
                if row < 0 and self.playlist.count() > 0:
                    row = 0
                self.play_item_at(row)
            else:
                self.mediaPlayer.play()

    # ------------------- Timeline / Seeking -------------------
    def on_duration_changed(self, duration_ms: int) -> None:
        self.positionSlider.setRange(0, int(duration_ms))
        self.labelDuration.setText(self._format_msec(duration_ms))

    def on_position_changed(self, position_ms: int) -> None:
        if not self._isSeeking:
            self.positionSlider.setValue(int(position_ms))
        # Always update current time label for immediate feedback
        self.labelCurrentTime.setText(self._format_msec(position_ms))

    def on_seek_started(self) -> None:
        self._isSeeking = True

    def on_seek_released(self) -> None:
        self._isSeeking = False
        self.mediaPlayer.setPosition(int(self.positionSlider.value()))

    def on_slider_moved(self, value: int) -> None:
        # Live update the current time label while dragging
        self.labelCurrentTime.setText(self._format_msec(int(value)))

    def _format_msec(self, msec: int) -> str:
        total_seconds = max(0, int(msec // 1000))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def on_slider_clicked(self, value: int) -> None:
        # Jump immediately to clicked position
        self._isSeeking = False
        self.mediaPlayer.setPosition(int(value))
        self.labelCurrentTime.setText(self._format_msec(int(value)))

    # ------------------- Volume / Mute -------------------
    def on_volume_changed(self, value: int) -> None:
        vol = max(0, min(100, int(value)))
        try:
            self.audioOutput.setVolume(vol / 100.0)
        except Exception:
            pass
        if vol > 0:
            self._lastNonZeroVolume = vol
            try:
                if self.audioOutput.isMuted():
                    self.audioOutput.setMuted(False)
            except Exception:
                pass
        else:
            try:
                self.audioOutput.setMuted(True)
            except Exception:
                pass
        self._update_mute_icon()

    def toggle_mute(self) -> None:
        try:
            new_muted = not self.audioOutput.isMuted()
            self.audioOutput.setMuted(new_muted)
            if not new_muted and self.volumeSlider.value() == 0:
                # Restore last non-zero volume on unmute
                self.volumeSlider.setValue(max(1, self._lastNonZeroVolume))
        except Exception:
            # Fallback: toggle based on slider if audioOutput lacks muted APIs
            if self.volumeSlider.value() > 0:
                self._lastNonZeroVolume = self.volumeSlider.value()
                self.volumeSlider.setValue(0)
            else:
                self.volumeSlider.setValue(max(1, self._lastNonZeroVolume))
        self._update_mute_icon()

    def _update_mute_icon(self) -> None:
        muted = False
        try:
            muted = bool(self.audioOutput.isMuted())
        except Exception:
            muted = self.volumeSlider.value() == 0
        self.muteButton.setIcon(self.iconVolumeMuted if muted else self.iconVolume)

    def _remove_playlist_item_by_path(self, file_path: str) -> int:
        """Remove the playlist item whose path matches file_path (normalized). Returns the row that was removed, or -1 if not found."""
        if not file_path:
            return -1
        norm = os.path.normcase(os.path.abspath(file_path))
        for i in range(self.playlist.count() - 1, -1, -1):
            item = self.playlist.item(i)
            p = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if p and os.path.normcase(os.path.abspath(p)) == norm:
                self.playlist.takeItem(i)
                return i
        return -1

    def delete_selected_files(self) -> None:
        rows = sorted({self.playlist.row(i) for i in self.playlist.selectedItems()}, reverse=True)
        if not rows:
            return

        current_file = self.mediaPlayer.source().toLocalFile()
        current_row_before = -1
        # Find the current row before deletion
        if current_file:
            norm_current = os.path.normcase(os.path.abspath(current_file))
            for i in range(self.playlist.count()):
                item = self.playlist.item(i)
                p = item.data(QtCore.Qt.ItemDataRole.UserRole)
                if p and os.path.normcase(os.path.abspath(p)) == norm_current:
                    current_row_before = i
                    break

        # If we're about to delete the currently playing file, release the handle first (Windows)
        if current_file and current_row_before in rows:
            self.mediaPlayer.stop()
            self.mediaPlayer.setSource(QtCore.QUrl())
            QtWidgets.QApplication.processEvents()

        removed_current = False

        for row in rows:
            item = self.playlist.item(row)
            file_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
            # Remove from UI first
            self.playlist.takeItem(row)
            # Delete file from filesystem (with retries on Windows when in use)
            if file_path:
                deleted = safe_delete_file(Path(file_path))
                if not deleted:
                    self.statusBar().showMessage(
                        f"Deleted from playlist; file in use: {file_path}. Delete manually if needed.",
                        6000,
                    )

            norm_current = os.path.normcase(os.path.abspath(current_file)) if current_file else ""
            if file_path and norm_current and os.path.normcase(os.path.abspath(file_path)) == norm_current:
                removed_current = True

        if removed_current and current_row_before >= 0:
            self.mediaPlayer.stop()
            # After removing current_row_before, the next item (which was at current_row_before + 1)
            # is now at current_row_before. Play at that index.
            if current_row_before < self.playlist.count():
                self.play_item_at(current_row_before)
            elif self.playlist.count() > 0:
                # If current_row_before was the last item, play the new last item
                self.play_item_at(self.playlist.count() - 1)

        # Ensure playlist still accepts drops even when empty
        self.playlist.setAcceptDrops(True)
        self._update_playlist_count()

    def save_selected_files(self) -> None:
        items = self.playlist.selectedItems()
        if not items:
            return
        current_file = self.mediaPlayer.source().toLocalFile()
        moved_current = False
        # Stop and release the file handle before moving (Windows keeps file locked until source is cleared)
        if current_file and any(
            item.data(QtCore.Qt.ItemDataRole.UserRole) == current_file for item in items
        ):
            self.mediaPlayer.stop()
            self.mediaPlayer.setSource(QtCore.QUrl())
            QtWidgets.QApplication.processEvents()

        # Get save directory (override or default from config)
        dest_dir = self.get_save_directory_for_session()

        # Work on a copy to avoid selection issues during removal
        rows = sorted({self.playlist.row(i) for i in items}, reverse=True)
        for row in rows:
            item = self.playlist.item(row)
            file_path = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if not file_path:
                continue
            src = Path(file_path)
            if not src.exists() or not src.is_file():
                continue

            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = unique_dest_path(dest_dir, src.name)

                copy_ok, source_removed = safe_move_file(src, dest)
                if not copy_ok:
                    raise OSError("Copy failed")
                # Remove from playlist by path so we always remove the right entry
                self._remove_playlist_item_by_path(file_path)
                if file_path == current_file:
                    moved_current = True
                if not source_removed:
                    self.statusBar().showMessage(
                        f"Saved to {dest}; original could not be removed (in use). Delete manually if needed.",
                        6000,
                    )
            except Exception as exc:
                logger.error(f"Failed to save file: {src}", exc_info=True)
                self.statusBar().showMessage(f"Failed to save: {src} ({exc})", 5000)

        if moved_current:
            # Playback already stopped above if current was in selection
            pass
        self._update_playlist_count()

    def save_current_and_play_next(self) -> None:
        """Save the currently playing file and automatically play next."""
        try:
            current_path = self.mediaPlayer.source().toLocalFile()
        except Exception:
            current_path = ""
        if not current_path:
            return
        src = Path(current_path)
        if not src.exists() or not src.is_file():
            return

        # Find the item in playlist
        current_row = -1
        for i in range(self.playlist.count()):
            it = self.playlist.item(i)
            if it.data(QtCore.Qt.ItemDataRole.UserRole) == current_path:
                current_row = i
                break

        # Stop and release the file handle so Windows can release the lock before we move
        self.mediaPlayer.stop()
        self.mediaPlayer.setSource(QtCore.QUrl())
        QtWidgets.QApplication.processEvents()

        # Get save directory (override or default from config)
        dest_dir = self.get_save_directory_for_session()

        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = unique_dest_path(dest_dir, src.name)

            copy_ok, source_removed = safe_move_file(src, dest)
            if not copy_ok:
                raise OSError("Copy failed")
            if not source_removed:
                self.statusBar().showMessage(
                    f"Saved to {dest}; original could not be removed (in use). Delete manually if needed.",
                    6000,
                )
            # Remove from playlist by path (in case current_row was wrong due to path format)
            removed_row = self._remove_playlist_item_by_path(current_path)
            if removed_row >= 0:
                if removed_row < self.playlist.count():
                    self.play_item_at(removed_row)
                elif self.playlist.count() > 0:
                    self.play_item_at(self.playlist.count() - 1)
                else:
                    self.mediaPlayer.stop()
            else:
                self.mediaPlayer.stop()
            self._update_playlist_count()
        except Exception as exc:
            logger.error(f"Failed to save file: {src}", exc_info=True)
            self.statusBar().showMessage(f"Failed to save: {src} ({exc})", 5000)

    def add_similar_for_selection(self) -> None:
        items = self.playlist.selectedItems()
        target_path: Optional[Path] = None
        if items:
            target_path = Path(items[0].data(QtCore.Qt.ItemDataRole.UserRole))
        else:
            # fallback to current playing file
            current = self.mediaPlayer.source().toLocalFile()
            if current:
                target_path = Path(current)
        if not target_path:
            return
        similar = find_similar_files(target_path)
        self.add_files(similar)

    def on_video_files_dropped(self, path_strs: List[str]) -> None:
        # Autoplay the first dropped video file. Do not modify playlist.
        for p in path_strs:
            pp = Path(p)
            if is_video_file(pp):
                url = QtCore.QUrl.fromLocalFile(str(pp))
                self.mediaPlayer.setSource(url)
                self.mediaPlayer.play()
                break
        else:
            # No playable video among dropped paths
            logger.warning("No playable video files found in dropped paths")
            self.statusBar().showMessage("No playable video in drop", 3000)
        # Update highlight even if the dropped file isn't in playlist
        self._highlight_current_in_playlist()

    # ------------------- Media callbacks -------------------
    def on_media_status_changed(self, status: QtMultimedia.QMediaPlayer.MediaStatus) -> None:
        if status == QtMultimedia.QMediaPlayer.MediaStatus.EndOfMedia:
            if not self.checkDoNotPlayNext.isChecked():
                self.play_next()
        elif status == QtMultimedia.QMediaPlayer.MediaStatus.InvalidMedia:
            # Skip unplayable files automatically without attempting any transcoding
            current = self.mediaPlayer.source().toLocalFile()
            if current:
                logger.warning(f"Cannot play invalid media file: {current}")
                self.statusBar().showMessage(f"Cannot play: {os.path.basename(current)} — skipping", 4000)
            if not self.checkDoNotPlayNext.isChecked():
                self.play_next()

    def on_playback_state_changed(self, state: QtMultimedia.QMediaPlayer.PlaybackState) -> None:
        if state == QtMultimedia.QMediaPlayer.PlaybackState.PlayingState:
            self.playButton.setIcon(self.iconPause)
        else:
            self.playButton.setIcon(self.iconPlay)

    # ------------------- Now Playing Highlight -------------------
    def _highlight_current_in_playlist(self) -> None:
        try:
            current_path = self.mediaPlayer.source().toLocalFile()
        except Exception:
            current_path = ""
        norm_current = os.path.normcase(os.path.abspath(current_path)) if current_path else ""
        for i in range(self.playlist.count()):
            item = self.playlist.item(i)
            p = item.data(QtCore.Qt.ItemDataRole.UserRole)
            is_current = bool(p and norm_current and os.path.normcase(os.path.abspath(p)) == norm_current)
            # Background color: light yellow for current, white otherwise
            bg = QtGui.QColor("#FFF7CC") if is_current else QtGui.QColor("white")
            item.setBackground(QtGui.QBrush(bg))
            # Font weight: bold for current, normal otherwise
            f = item.font()
            f.setBold(bool(is_current))
            item.setFont(f)
        self._update_playlist_count()

    def _update_playlist_count(self) -> None:
        total = self.playlist.count()
        current_row = self.current_row()
        current_num = current_row + 1 if current_row >= 0 else 0
        self.labelPlaylistCount.setText(f"{current_num}/{total}")
        self._update_save_path()

    def get_save_directory_for_session(self) -> Path:
        """Return override folder if set, otherwise the default from config."""
        override = self.lineEditOverrideSave.text().strip()
        if override:
            return Path(override)
        return get_saved_directory()

    def _update_save_path(self) -> None:
        """Update the save path label based on the effective saved directory."""
        if self.playlist.count() == 0:
            self.labelSavePath.setText("")
            return
        save_target_dir = self.get_save_directory_for_session()
        self.labelSavePath.setText(f"Save to: {save_target_dir}")
