# main.py
import sys, os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from ui_panel import ControlPanel
from draw_overlay import HealthZoneOverlay
from config import RES_GEOMETRY


def resource_path(rel_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    icon = QIcon(resource_path("assets/app.ico"))
    app.setWindowIcon(icon)

    panel = ControlPanel()
    panel.setWindowIcon(icon)
    panel.show()

    geo = RES_GEOMETRY[panel.resolution_text]
    overlay = HealthZoneOverlay(geo, controller=panel)
    panel.linked_overlay = overlay            

    panel.destroyed.connect(app.quit)
    sys.exit(app.exec_())
