from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List
from widgets.playlist_widget import PlaylistWidget
from widgets.video_widget import DroppableVideoWidget
from widgets.slider_widget import SeekSlider
from widgets.mainwindow_widget import MainWindow


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


