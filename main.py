import argparse
import sys
from PyQt6 import QtWidgets
from widgets.mainwindow_widget import MainWindow
from logger import setup_logger


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PyQt6 Video Player with Playlist",
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
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


