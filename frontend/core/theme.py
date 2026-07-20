"""
core/theme.py
负责加载并应用 QSS 主题样式表。
"""
from PyQt6.QtWidgets import QApplication

from core.config import THEMES_DIR

THEME_FILES = {
    "silk": "silk.qss",
    "dark": "dark.qss",
    "light": "light.qss",
}

THEME_LABELS = {
    "silk": "丝绸主题（默认）",
    "dark": "暗夜主题",
    "light": "晴日主题",
}


def available_themes() -> list[str]:
    return list(THEME_FILES.keys())


def apply_theme(app: QApplication, theme_name: str) -> None:
    """将指定主题应用到整个应用程序。"""
    filename = THEME_FILES.get(theme_name, THEME_FILES["silk"])
    qss_path = THEMES_DIR / filename
    if not qss_path.exists():
        return
    try:
        stylesheet = qss_path.read_text(encoding="utf-8")
        app.setStyleSheet(stylesheet)
    except OSError:
        pass
