"""
main.py
Entry point de Impositor A5.
"""

import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow

APP_VERSION = "1.0.0"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Impositor A5")
    app.setApplicationVersion(APP_VERSION)

    window = MainWindow(app_version=APP_VERSION)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
