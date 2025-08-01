
# config.py

RES_GEOMETRY = {
    "1920x1080 (1080p)": (753, 1030, 414, 20),
    "2560x1440 (2K)": (1004, 1372, 552, 27),
    "3840x2160 (4K)": (1507, 2060, 828, 41),
}

ZONE_DAMAGE = {1: 0.4, 2: 0.6, 3: 0.8, 4: 1, 5: 3, 6: 5, 7: 7, 8: 9, 9: 11}

ZONE_TIMINGS = [
    (1, 240, 270), (2, 120, 90), (3, 100, 80),
    (4, 100, 80), (5, 100, 60), (6, 90, 30),
    (7, 70, 30), (8, 60, 30), (9, 60, 30)
]

TOLERANCE_MAP = {
    "老师傅": 0,
    "激进": lambda lvl: ZONE_DAMAGE.get(lvl, 0) + 1,
    "正常": lambda lvl: ZONE_DAMAGE.get(max(1, lvl - 2), 0) + ZONE_DAMAGE.get(lvl, 0) + 2,
    "保守": lambda lvl: ZONE_DAMAGE.get(max(1, lvl - 1), 0) + ZONE_DAMAGE.get(max(1, lvl - 2), 0) + ZONE_DAMAGE.get(lvl, 0) + 3,
}
