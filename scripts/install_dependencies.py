#!/usr/bin/env python3
"""
scripts/install_dependencies.py
跨平台依赖安装辅助脚本：检测操作系统并给出（或尝试执行）相应的安装命令。
不会在没有网络 / 没有 sudo 权限时静默失败——始终打印出手动安装的命令供用户参考。
"""
import platform
import shutil
import subprocess
import sys


def run(cmd: list[str]) -> bool:
    print(f"$ {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  执行失败: {e}")
        return False


def main():
    system = platform.system()
    print(f"检测到操作系统: {system}\n")

    print("== Python 依赖 (PyQt6, requests) ==")
    run([sys.executable, "-m", "pip", "install", "-r", "frontend/requirements.txt"])

    print("\n== C++ 构建依赖 ==")
    if system == "Linux":
        if shutil.which("apt"):
            print("检测到 apt，建议执行:")
            print("  sudo apt install -y build-essential cmake libcurl4-openssl-dev python3-dev")
        elif shutil.which("pacman"):
            print("检测到 pacman，建议执行:")
            print("  sudo pacman -S --needed base-devel cmake curl python")
        elif shutil.which("dnf"):
            print("检测到 dnf，建议执行:")
            print("  sudo dnf install -y gcc-c++ cmake libcurl-devel python3-devel")
        else:
            print("未识别的包管理器，请手动安装: cmake, g++, libcurl 开发包, python3-dev")
    elif system == "Darwin":
        print("建议使用 Homebrew:")
        print("  brew install cmake curl")
    elif system == "Windows":
        print("建议安装:")
        print("  1. Visual Studio 2022 (含 C++ 桌面开发工作负载)")
        print("  2. CMake: https://cmake.org/download/")
        print("  3. vcpkg 安装 curl: vcpkg install curl")
    else:
        print("未知操作系统，请参考 README.md 手动安装依赖。")

    print("\n依赖准备完成后，运行 ./build.sh 进行完整构建。")


if __name__ == "__main__":
    main()
