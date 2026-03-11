#!/usr/bin/env python3
"""
SeisLab - Professional Seismic Analysis and Attribute Extraction GUI
Main Application Entry Point
"""

import sys

from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QTimer

from gui.separate_gui_for_seismic import SeisLabApp


def main():

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    app.setApplicationName("SeisLab")
    app.setOrganizationName("SeisLab")

    app.setStyle("Fusion")

    # App icon
    app_icon = QIcon("images/seislab.png")
    app.setWindowIcon(app_icon)

    # Splash screen
    splash_pix = QPixmap("images/seislab.png")
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setWindowFlag(Qt.FramelessWindowHint)
    splash.show()

    splash.showMessage(
        "Initializing SeisLab...",
        Qt.AlignBottom | Qt.AlignCenter,
        Qt.white
    )
    splash.showMessage("Loading seismic modules...")
    splash.showMessage("Initializing attribute engine...")
    splash.showMessage("Preparing GUI...")

    app.processEvents()

    # Create main window
    window = SeisLabApp()
    window.setWindowIcon(app_icon)

    # Show main window after 3 seconds
    def start_main():
        window.show()
        splash.finish(window)

    QTimer.singleShot(3000, start_main)   # 3000 ms = 3 seconds

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
