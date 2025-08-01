# zone_timer.py
from PyQt5.QtCore import QObject, QTimer, QDateTime
from config import ZONE_TIMINGS


class ZoneTimer(QObject):
    """核心计时逻辑，已从 ui_panel.py 抽离出来。

    - 管理倒计时 / 缩圈阶段切换
    - 同步 parent(ControlPanel) 的 zone_level，并刷新覆盖层
    - 在关键节点调用 voice 播报
    """

    def __init__(self, panel):
        super().__init__(panel)
        self.panel = panel

        self._qt_timer = QTimer(self)
        self._qt_timer.setInterval(200)
        self._qt_timer.timeout.connect(self._tick)

        self._reset_state()


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
        self.sync_time = QDateTime.currentDateTime().addSecs(-1)


        if hasattr(self.panel, "linked_overlay"):
            self.panel.linked_overlay.update()
        self._tick()

        self._qt_timer.start()

    def stop(self):
        self._qt_timer.stop()


    def _tick(self):
        if not self.sync_time:
            return

        elapsed = self.sync_time.secsTo(QDateTime.currentDateTime())
        total = self.remaining_seconds - elapsed
        int_total = int(total)

        if self.sync_phase == "shrinking":
            next_stage = self.zone_level + 1
            if (
                next_stage not in self._played_pre_stage and
                self._prev_total is not None and self._prev_total > 8 >= int_total
            ):
                self.panel.voice.play_pre_stage(next_stage)
                self._played_pre_stage.add(next_stage)
        self._prev_total = int_total


        if total <= 0:
            if self.sync_phase == "countdown":
                self.sync_phase = "shrinking"
                self.sync_time = QDateTime.currentDateTime()
                self.remaining_seconds = ZONE_TIMINGS[self.sync_index][2]
            else:
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
