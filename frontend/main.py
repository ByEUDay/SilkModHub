#!/usr/bin/env python3
"""
SilkModHub · 丝之歌 Mod 管理器
入口文件
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication

from core.backend import Backend, NATIVE_AVAILABLE
from core.config import ASSETS_DIR
from core.theme import apply_theme
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SilkModHub")
    app.setStyle("Fusion")

    icon_path = ASSETS_DIR / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    font = QFont("Microsoft YaHei UI", 10)
    app.setFont(font)

    if not NATIVE_AVAILABLE:
        print("[提示] 未检测到已编译的 C++ 后端模块 silk_backend，"
              "当前使用纯 Python 回退实现（功能一致，性能略低）。\n"
              "运行 build.sh 以启用高性能 C++ 后端。")

    backend = Backend()
    apply_theme(app, backend.config.theme)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
