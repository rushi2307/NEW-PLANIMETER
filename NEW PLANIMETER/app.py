"""
New Planimeter - Application Entry Point
PC-based engineering application for measuring the area of irregular plots from 2D images
and integrating measured geometry with AutoCAD.
"""

import sys
import os

# Ensure local project directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from gui.main_window import MainWindow


def main():
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("New Planimeter")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Engineering Solutions")

    # Set default application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
