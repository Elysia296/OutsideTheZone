# voice.py
import os
import sys
import sip
from PyQt5.QtCore import QObject, QTimer, QUrl
from PyQt5.QtMultimedia import QSoundEffect


def resource_path(relative_path: str) -> str:
    """兼容 PyInstaller 的资源路径"""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


class VoiceManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.voice_dir = resource_path("voice")

        # 正在播放的音效与延迟任务
        self._effects = set()     # {QSoundEffect}
        self._delayed = []        # [QTimer]

        self._enabled = True
        self._volume = 1.0

    # ------------ 外部控制 ------------
    def set_enabled(self, enabled: bool):
        self._enabled = bool(enabled)

    def set_volume(self, volume01: float):
        self._volume = max(0.0, min(1.0, volume01))
        for eff in list(self._effects):
            try:
                if not sip.isdeleted(eff):
                    eff.setVolume(self._volume)
            except Exception:
                pass

    def reset(self):
        """立即停止所有正在播放或排程中的语音，并安全清理资源。"""
        # 1) 取消所有延迟任务（如“10秒倒计时”的预约）
        for t in self._delayed:
            try:
                t.stop()
                t.deleteLater()
            except Exception:
                pass
        self._delayed.clear()

        # 2) 停止/删除所有正在播放的音效
        for eff in list(self._effects):
            try:
                if sip.isdeleted(eff):
                    continue
                # 断开信号，防止回调里再次触发清理
                try:
                    eff.playingChanged.disconnect()
                except Exception:
                    pass
                eff.stop()
                eff.deleteLater()
            except Exception:
                pass
            finally:
                if eff in self._effects:
                    self._effects.remove(eff)

    # ------------ 业务播报 ------------
    def play_pre_stage(self, next_stage: int):
        """缩圈中：距离进入下一阶段还剩 8 秒的提示。"""
        if not (5 <= next_stage <= 9):
            return
        fname = (
            "剩余8秒进入阶段9超距锁定.wav"
            if next_stage == 9 else
            f"剩余8秒进入阶段{next_stage}.wav"
        )
        self._play(fname)

    def play_stage9_start(self):
        """阶段9开始的提示，同时预约 20 秒后播放“10秒倒计时”。"""
        self._play("阶段9锁定开始.wav")

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(20_000)
        timer.timeout.connect(lambda: self._play("10秒倒计时.wav"))
        timer.start()
        self._delayed.append(timer)

    # ------------ 底层播放 ------------
    def _play(self, filename: str):
        if not self._enabled:
            return
        path = os.path.join(self.voice_dir, filename)
        if not os.path.isfile(path):
            return

        eff = QSoundEffect(self)
        eff.setSource(QUrl.fromLocalFile(path))
        eff.setLoopCount(1)
        eff.setVolume(self._volume)

        # 用 playingChanged 监听结束并做一次性清理（避免二次 deleteLater）
        def _on_playing_changed():
            try:
                if sip.isdeleted(eff):
                    return
                if not eff.isPlaying():
                    if eff in self._effects:
                        self._effects.remove(eff)
                    try:
                        eff.playingChanged.disconnect(_on_playing_changed)
                    except Exception:
                        pass
                    eff.deleteLater()
            except Exception:
                pass

        eff.playingChanged.connect(_on_playing_changed)
        self._effects.add(eff)
        eff.play()
