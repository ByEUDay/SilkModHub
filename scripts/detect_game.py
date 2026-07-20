#!/usr/bin/env python3
"""
scripts/detect_game.py
独立小工具：命令行下测试游戏路径自动检测，方便调试而无需启动整个 GUI。

用法:
    python3 scripts/detect_game.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "frontend"))

from core.backend import Backend              


def main():
    backend = Backend()
    print(f"当前后端: {'C++ 原生扩展' if _native_available() else '纯 Python 回退实现'}")

    install = backend.detect_game()
    if install and install.valid:
        print(f"✅ 检测成功")
        print(f"   路径: {install.path}")
        print(f"   来源: {install.source}")
        print(f"   可执行文件: {install.executable}")
    else:
        print("⚠ 未自动检测到《丝之歌》安装目录。")
        manual = input("请输入游戏安装目录进行手动校验（留空跳过）: ").strip()
        if manual:
            result = backend.validate_manual_path(manual)
            print("✅ 有效" if result.valid else "❌ 无效：未找到可执行文件")


def _native_available() -> bool:
    from core.backend import NATIVE_AVAILABLE
    return NATIVE_AVAILABLE


if __name__ == "__main__":
    main()
