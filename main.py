"""
Slop Video Sorter

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
import argparse
import sys
from pathlib import Path
from PyQt6 import QtWidgets, QtGui
from widgets.mainwindow_widget import MainWindow
from logger import setup_logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Slop Video Sorter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (can be used multiple times: -v, -vv, -vvv for WARNING, INFO, DEBUG)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # Set up logging with verbosity level
    setup_logger(verbosity=args.verbose)
    
    app = QtWidgets.QApplication(sys.argv)
    
    # Set application icon
    icon_path = Path(__file__).parent / "icons/icon_128.png"
    if icon_path.exists():
        app.setWindowIcon(QtGui.QIcon(str(icon_path)))
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


