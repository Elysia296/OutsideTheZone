# draw_overlay.py
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt

from config import ZONE_DAMAGE, TOLERANCE_MAP


class HealthZoneOverlay(QWidget):
    def __init__(self, geometry, controller):
        super().__init__()
        self.controller = controller

        self.setGeometry(*geometry)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.show()


    def calculate_thresholds(self, zl, mode_name):
        base = ZONE_DAMAGE.get(zl, 0)
        p1 = ZONE_DAMAGE.get(max(1, zl - 1), 0)
        p2 = ZONE_DAMAGE.get(max(1, zl - 2), 0)
        x = TOLERANCE_MAP[mode_name]
        x = x(zl) if callable(x) else x
        return (
            base * 6 + x,                      
            (base + p2) * 6 + x,               
            (base + p1 + p2) * 6 + x if zl < 8 else None,  
            x                                  
        )


    @staticmethod
    def draw_colored_line(painter, xpos, top, bottom, color):
        painter.setPen(QPen(QColor(0, 0, 0), 4))
        painter.drawLine(xpos, top, xpos, bottom)
        painter.setPen(QPen(color, 2))
        painter.drawLine(xpos, top, xpos, bottom)


    def paintEvent(self, event):
        if not getattr(self.controller, "guides_enabled", True):
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        top, bot = -4, h + 4
        zl = self.controller.zone_level
        mode = self.controller.tolerance_mode

        if zl == 9:
            painter.setFont(QFont("微软雅黑", 12, QFont.Bold))
            specials = [
                (0.25, "急救包", QColor(255, 0, 0)),    
                (0.50, "医疗箱", QColor(0, 255, 0)),    
            ]
            for ratio, label, color in specials:
                xpos = int(w * ratio)
                self.draw_colored_line(painter, xpos, top, bot, color)
                painter.setPen(color)
                painter.drawText(xpos + 6, 22, label)
            return


        no, l1, l2, x = self.calculate_thresholds(zl, mode)

        self.draw_colored_line(painter, int(w * min(1.0, no / 100)), top, bot, QColor(128, 0, 128))
        if zl >= 3:
            self.draw_colored_line(painter, int(w * min(1.0, l1 / 100)), top, bot, QColor(0, 128, 255))
            if l2:
                self.draw_colored_line(painter, int(w * min(1.0, l2 / 100)), top, bot, QColor(0, 255, 0))
        self.draw_colored_line(painter, int(w * min(1.0, x / 100)), top, bot, QColor(0, 0, 0))
