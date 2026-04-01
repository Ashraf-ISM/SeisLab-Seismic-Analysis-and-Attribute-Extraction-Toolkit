import os
import sys

from PyQt5.QtWidgets import QApplication

# Ensure project root is available for standalone execution.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from gui.petrophysics.controller import PetrophysicsWorkstationController


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Petrophysics Workstation")
    app.setStyle("Fusion")

    window = PetrophysicsWorkstationController()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
