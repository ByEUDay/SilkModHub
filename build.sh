#!/usr/bin/env bash
# SilkModHub 一键构建脚本
# 需要网络连接（CMake FetchContent 会拉取 nlohmann/json, miniz, pybind11）
set -e

echo "==> 检查依赖..."
command -v cmake >/dev/null || { echo "请先安装 cmake"; exit 1; }
command -v python3 >/dev/null || { echo "请先安装 python3"; exit 1; }

# libcurl 开发包 (Debian/Ubuntu: libcurl4-openssl-dev)
if ! ldconfig -p 2>/dev/null | grep -q libcurl; then
    echo "警告: 未检测到 libcurl，请先安装（Debian/Ubuntu: sudo apt install libcurl4-openssl-dev）"
fi

echo "==> 安装 Python 依赖..."
pip3 install -r frontend/requirements.txt

echo "==> 配置 CMake..."
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

echo "==> 编译 C++ 后端 + pybind11 绑定..."
cmake --build build -j"$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)"

echo "==> 构建完成！运行方式："
echo "    cd frontend && python3 main.py"
