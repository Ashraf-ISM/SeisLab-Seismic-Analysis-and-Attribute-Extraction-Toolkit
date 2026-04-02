import os
import sys

# Ensure project root is available for standalone execution.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Qt needs an OpenGL backend on some Linux setups; prefer software rendering
# and a headless platform when no display server is available.
os.environ.setdefault("QT_OPENGL", "software")
if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt5.QtWidgets import QApplication
except ImportError as exc:
    if "libGL.so.1" in str(exc):
        sys.stderr.write(
            "PyQt5 could not start because libGL.so.1 is missing. "
            "Install it on Ubuntu/Debian with: sudo apt-get update && sudo apt-get install -y libgl1\n"
        )
    raise

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
