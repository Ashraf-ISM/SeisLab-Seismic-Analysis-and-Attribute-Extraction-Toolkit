#!/usr/bin/env python3
"""
SeisLab - Professional Seismic Analysis and Attribute Extraction GUI
Main Application Entry Point
"""

import sys
import time

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt

from gui.main_window import SeisLabApp


def main():
    """Initialize and run the SeisLab application."""

    # Enable High DPI scaling (important for modern displays)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Application metadata
    app.setApplicationName("SeisLab")
    app.setOrganizationName("SeisLab")

    # Set application style
    app.setStyle("Fusion")

    # -------------------------------
    # Set App Icon
    # -------------------------------
    app_icon = QIcon("images/seislab.png")
    app.setWindowIcon(app_icon)

    # -------------------------------
    # Splash Screen (Startup Logo)
    # -------------------------------
    splash_pix = QPixmap("images/seislab.png")

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setWindowFlag(Qt.FramelessWindowHint)
    splash.show()

    splash.showMessage(
        "Initializing SeisLab...",
        Qt.AlignBottom | Qt.AlignCenter,
        Qt.white
    )

    # Process events so splash appears immediately
    app.processEvents()

    # Simulated loading delay (optional)
    time.sleep(1.5)

    # -------------------------------
    # Main Window
    # -------------------------------
    window = SeisLabApp()
    window.setWindowIcon(app_icon)

    window.show()

    # Close splash after window loads
    splash.finish(window)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()