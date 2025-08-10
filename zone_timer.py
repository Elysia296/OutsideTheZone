# zone_timer.py
from PyQt5.QtCore import QObject, QTimer, QDateTime
from config import ZONE_TIMINGS


class ZoneTimer(QObject):
    """核心计时逻辑。"""

    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel

        self._qt_timer = QTimer(self)
        self._qt_timer.setInterval(200)
        self._qt_timer.timeout.connect(self._tick)

        self._reset_state()

    # ---- 对外接口 ----
    def start(self, stage_idx: int, countdown_seconds: int):
        """开始计时。

        Args:
            stage_idx: 0‑based 阶段索引（0 → 阶段1）。
            countdown_seconds: 距离开始缩圈的秒数。
        """
        self._reset_state()
        self.sync_index = stage_idx
        self.zone_level = ZONE_TIMINGS[stage_idx][0]
        self.panel.zone_level = self.zone_level  # Mirror to UI

        self.remaining_seconds = countdown_seconds
        self.sync_time = QDateTime.currentDateTime()

        if hasattr(self.panel, "linked_overlay"):
            self.panel.linked_overlay.update()
        self._tick()

        self._qt_timer.start()

    def stop(self):
        self._qt_timer.stop()

    def reset(self):
        """完全复位：停止计时并清空内部状态。"""
        self.stop()
        self._reset_state()
        # 同步面板显示
        self.panel.zone_level = 1
        if hasattr(self.panel, "linked_overlay"):
            self.panel.linked_overlay.update()

    # ---- 内部逻辑 ----
    def _tick(self):
        if not self.sync_time:
            return

        elapsed = self.sync_time.secsTo(QDateTime.currentDateTime())
        total = self.remaining_seconds - elapsed
        int_total = int(total)

        # 仅在“缩圈中”监测 8 秒播报
        if self.sync_phase == "shrinking":
            next_stage = self.zone_level + 1
            if (
                next_stage not in self._played_pre_stage and
                self._prev_total is not None and self._prev_total > 8 >= int_total
            ):
                self.panel.voice.play_pre_stage(next_stage)
                self._played_pre_stage.add(next_stage)
        self._prev_total = int_total

        # 阶段/相位切换判定
        if total <= 0:
            if self.sync_phase == "countdown":
                # 开始缩圈
                self.sync_phase = "shrinking"
                self.sync_time = QDateTime.currentDateTime()
                self.remaining_seconds = ZONE_TIMINGS[self.sync_index][2]
            else:
                # 缩圈结束 -> 进入下一阶段倒计时
                self.sync_index += 1
                if self.sync_index < len(ZONE_TIMINGS):
                    self.sync_phase = "countdown"
                    self.sync_time = QDateTime.currentDateTime()
                    self.remaining_seconds = ZONE_TIMINGS[self.sync_index][1]
                    self.zone_level = ZONE_TIMINGS[self.sync_index][0]
                    self.panel.zone_level = self.zone_level

                    if self.zone_level == 9 and not self._played_stage9_started:
                        self.panel.voice.play_stage9_start()
                        self._played_stage9_started = True

                    if hasattr(self.panel, "linked_overlay"):
                        self.panel.linked_overlay.update()
                else:
                    # 全流程完成
                    self.stop()
                    self.panel.info_label.setText("阶段 10 已结束")
                    return
            total = self.remaining_seconds
            int_total = int(total)

        m, s = divmod(max(0, int_total), 60)
        label = "倒计时" if self.sync_phase == "countdown" else "缩圈中"
        new_txt = f"当前阶段：{self.zone_level}，{label}：{m:02d}:{s:02d}"
        if new_txt != self._last_display:
            self.panel.info_label.setText(new_txt)
            self._last_display = new_txt

    def _reset_state(self):
        self.sync_time = None
        self.sync_index = 0
        self.zone_level = 1
        self.remaining_seconds = 0
        self.sync_phase = "countdown"
        self._last_display = ""
        self._played_pre_stage = set()
        self._played_stage9_started = False
        self._prev_total = None
