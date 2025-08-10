# ui_panel.py
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QComboBox, QHBoxLayout,
    QPushButton, QLineEdit, QMessageBox, QCheckBox, QSlider,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QGuiApplication

from config import RES_GEOMETRY, TOLERANCE_MAP, ZONE_TIMINGS
from voice import VoiceManager
from zone_timer import ZoneTimer


class ControlPanel(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("抗毒小助手")
        self.setFixedSize(680, 680)
        self.is_synced = False

        base_font = QFont("微软雅黑", 20)
        self.setFont(base_font)

        self.setStyleSheet("""
            QWidget { background-color: #F5F5F7; border-radius: 24px; }
            QLabel  { color: #2E2E2E; font-size: 20px; }
            QLineEdit, QComboBox {
                background: #FFFFFF; border: 1px solid #C8C8C8;
                border-radius: 8px; padding: 12px; font-size: 20px;
            }
            QComboBox::drop-down { subcontrol-origin: padding; subcontrol-position: top right;
                                    width: 40px; border-left: none; }
            QComboBox::down-arrow { width: 20px; height: 20px; }
            QComboBox QAbstractItemView {
                background: #FFFFFF; border: 1px solid #C8C8C8; border-radius: 8px;
                selection-background-color: #E6E0FF; font-size: 20px;
            }
            QComboBox QAbstractItemView::item { padding: 14px 18px; }
            QComboBox QAbstractItemView::item:selected {
                background: #E6E0FF; color: #4A31A2;
            }
            QPushButton {
                background-color: #6C63FF; color: #FFFFFF; border: none;
                border-radius: 20px; padding: 16px 36px; font-size: 22px;
            }
            QPushButton:hover { background-color: #5751D1; }
            QCheckBox { font-size: 20px; }

            /* 圆形滑块把手 */
            QSlider::groove:horizontal {
                background: #C8C8C8; height: 6px; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #6C63FF; border: none; width: 20px; height: 20px;
                margin: -7px 0; border-radius: 10px;
            }
        """)

        # --- 状态 ---
        self.zone_level = 1
        self.tolerance_mode = "正常"
        self.resolution_text = "2560x1440 (2K)"
        self.guides_enabled = True

        # --- 组件 ---
        self.voice = VoiceManager(self)
        self.zone_timer = ZoneTimer(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(26)

        # 分辨率
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("分辨率："))
        self.res_combo = QComboBox(); self.res_combo.setFont(base_font); self.res_combo.setFixedHeight(60)
        self.res_combo.addItems(RES_GEOMETRY.keys())
        # 启动时自动检测并选中
        autodetected = self.auto_detect_resolution()
        if autodetected:
            self.resolution_text = autodetected
        self.res_combo.setCurrentText(self.resolution_text)
        self.res_combo.currentTextChanged.connect(self.update_resolution)
        row1.addWidget(self.res_combo)
        layout.addLayout(row1)

        # 阶段选择
        self.row_stage = QHBoxLayout()
        self.row_stage.addWidget(QLabel("选择阶段："))
        self.stage_combo = QComboBox(); self.stage_combo.setFont(base_font); self.stage_combo.setFixedHeight(60)
        self.stage_combo.addItems([f"阶段 {i}" for i in range(1, 10)])
        self.row_stage.addWidget(self.stage_combo)
        layout.addLayout(self.row_stage)

        # 倒计时输入
        self.row_timer = QHBoxLayout()
        self.row_timer.addWidget(QLabel("距离缩圈开始剩余：<span style='color: rgba(217,83,79,0);'>____________</span>"))
        self.minute_input = QLineEdit("3"); self.minute_input.setFixedHeight(60)
        self.row_timer.addWidget(self.minute_input); self.row_timer.addWidget(QLabel("分"))
        self.second_input = QLineEdit("0"); self.second_input.setFixedHeight(60)
        self.row_timer.addWidget(self.second_input); self.row_timer.addWidget(QLabel("秒"))
        layout.addLayout(self.row_timer)

        # 容错
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("容错模式："))
        self.mode_combo = QComboBox(); self.mode_combo.setFont(base_font); self.mode_combo.setFixedHeight(60)
        self.mode_combo.addItems(list(TOLERANCE_MAP.keys()))
        self.mode_combo.setCurrentText(self.tolerance_mode)
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        row4.addWidget(self.mode_combo)
        layout.addLayout(row4)

        # 语音 & 音量
        row5 = QHBoxLayout()
        self.voice_chk = QCheckBox("启用语音提示")
        self.voice_chk.setChecked(True)
        self.voice_chk.stateChanged.connect(lambda st: self.voice.set_enabled(st == Qt.Checked))
        row5.addWidget(self.voice_chk)

        vol_label = QLabel("音量：")
        vol_label.setContentsMargins(120, 0, 0, 0)
        row5.addWidget(vol_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(200)
        self.volume_slider.valueChanged.connect(lambda v: self.voice.set_volume(v / 100.0))
        row5.addWidget(self.volume_slider)
        layout.addLayout(row5)

        # 其它选项
        row6 = QHBoxLayout()
        self.guides_chk = QCheckBox("启用辅助线")
        self.guides_chk.setChecked(True)
        self.guides_chk.stateChanged.connect(self.on_guides_toggled)
        row6.addWidget(self.guides_chk)

        self.auto_min_chk = QCheckBox("同步后自动最小化"); self.auto_min_chk.setChecked(False)
        row6.addWidget(self.auto_min_chk)
        layout.addLayout(row6)

        # 同步按钮
        btn_row = QHBoxLayout()
        self.sync_btn = QPushButton("同步"); self.sync_btn.setFont(QFont("微软雅黑", 22)); self.sync_btn.setFixedHeight(64)
        self.sync_btn.clicked.connect(self.sync)
        btn_row.addWidget(self.sync_btn)

        self.resync_btn = QPushButton("重新同步"); self.resync_btn.setFont(QFont("微软雅黑", 22)); self.resync_btn.setFixedHeight(64)
        self.resync_btn.clicked.connect(self.resync); self.resync_btn.hide()
        btn_row.addWidget(self.resync_btn)
        layout.addLayout(btn_row)

        # 信息
        self.info_label = QLabel("当前阶段：未同步"); self.info_label.setFont(QFont("微软雅黑", 20, QFont.Bold))
        layout.addWidget(self.info_label, alignment=Qt.AlignCenter)

        self._stage_widgets = [w for i in range(self.row_stage.count()) if (w := self.row_stage.itemAt(i).widget())]
        self._timer_widgets = [w for i in range(self.row_timer.count()) if (w := self.row_timer.itemAt(i).widget())]

    # -------- 自动分辨率检测 --------
    def auto_detect_resolution(self) -> str:
        """返回匹配到的 RES_GEOMETRY key，否则返回空字符串。"""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return ""
        g = screen.geometry()
        w, h = g.width(), g.height()

        # 以 "WxH" 前缀匹配 keys
        wanted = f"{w}x{h}"
        for key in RES_GEOMETRY.keys():
            if key.startswith(wanted):
                return key
        # 没有精确匹配时不改动
        return ""

    # -------- 交互逻辑 --------
    def update_resolution(self, text: str):
        self.resolution_text = text
        if hasattr(self, "linked_overlay"):
            self.linked_overlay.setGeometry(*RES_GEOMETRY[self.resolution_text])

    def on_mode_changed(self, text: str):
        self.tolerance_mode = text
        if text == "老师傅":
            QMessageBox.information(self, "温馨提示", "仅为理论极限，切勿卡线打药。")
        if hasattr(self, "linked_overlay"):
            self.linked_overlay.update()

    def on_guides_toggled(self, state):
        self.guides_enabled = (state == Qt.Checked)
        if hasattr(self, "linked_overlay"):
            self.linked_overlay.update()

    def sync(self):
        # 开始前先清理任何遗留的语音排程，避免串音
        self.voice.reset()

        try:
            m = int(self.minute_input.text()); s = int(self.second_input.text())
        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的分钟和秒数！"); return
        total = m * 60 + s

        stage_idx = self.stage_combo.currentIndex(); max_wait = ZONE_TIMINGS[stage_idx][1]
        if total > max_wait:
            mm, ss = divmod(max_wait, 60)
            QMessageBox.warning(self, "倒计时过长", f"阶段 {stage_idx + 1} 最大等待为 {mm} 分 {ss:02d} 秒！")
            return

        self.zone_timer.start(stage_idx, total)

        for w in self._stage_widgets + self._timer_widgets:
            w.setVisible(False)
        self.sync_btn.hide(); self.resync_btn.show()

        if self.auto_min_chk.isChecked():
            self.showMinimized()

        self.is_synced = True
        if hasattr(self, "linked_overlay"):
            self.linked_overlay.update()

    def resync(self):
        # 立刻停止计时与所有语音内部倒计时
        self.zone_timer.stop()
        self.voice.reset()

        for w in self._stage_widgets + self._timer_widgets:
            w.setVisible(True)
        self.resync_btn.hide(); self.sync_btn.show()

        self.info_label.setText("当前阶段：未同步")

        self.is_synced = False
        if hasattr(self, "linked_overlay"):
            self.linked_overlay.update()
