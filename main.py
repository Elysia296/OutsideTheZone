# main.py
import sys, os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from ui_panel import ControlPanel
from draw_overlay import HealthZoneOverlay
from config import RES_GEOMETRY


def resource_path(rel_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, rel_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 兼容打包后的图标路径
    icon_path = resource_path("assets/app.ico")
    if os.path.isfile(icon_path):
        icon = QIcon(icon_path)
        app.setWindowIcon(icon)
    else:
        icon = QIcon()

    panel = ControlPanel()
    if not icon.isNull():
        panel.setWindowIcon(icon)
    panel.show()

    geo = RES_GEOMETRY[panel.resolution_text]
    overlay = HealthZoneOverlay(geo, controller=panel)
    panel.linked_overlay = overlay

    panel.destroyed.connect(app.quit)
    sys.exit(app.exec_())
