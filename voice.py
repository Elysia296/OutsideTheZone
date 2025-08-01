# voice.py

import os
from PyQt5.QtCore import QObject, QTimer, QUrl
from PyQt5.QtMultimedia import QSoundEffect


class VoiceManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.voice_dir = os.path.join(os.path.dirname(__file__), "voice")
        self._cache = []
        self._enabled = True           
        self._volume = 1.0             



    def set_enabled(self, enabled: bool):
        """启用 / 禁用语音"""
        self._enabled = bool(enabled)

    def set_volume(self, volume01: float):
        """调整全局音量（0.0~1.0）"""
        self._volume = max(0.0, min(1.0, volume01))

    def play_pre_stage(self, next_stage: int):
        if not (5 <= next_stage <= 9):
            return
        fname = (
            "剩余8秒进入阶段9超距锁定.wav"
            if next_stage == 9 else
            f"剩余8秒进入阶段{next_stage}.wav"
        )
        self._play(fname)

    def play_stage9_start(self):
        self._play("阶段9锁定开始.wav")
        QTimer.singleShot(20_000, lambda: self._play("10秒倒计时.wav"))


    def _play(self, filename: str):
        if not self._enabled:
            return
        path = os.path.join(self.voice_dir, filename)
        if not os.path.isfile(path):
            return

        effect = QSoundEffect(self)
        effect.setSource(QUrl.fromLocalFile(path))
        effect.setLoopCount(1)
        effect.setVolume(self._volume)
        effect.play()

        self._cache.append(effect)
        QTimer.singleShot(
            10_000,
            lambda eff=effect: self._cache.remove(eff) if eff in self._cache else None,
        )
