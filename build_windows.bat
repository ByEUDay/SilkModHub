@echo off
chcp 65001 >nul
REM SilkModHub 一键构建脚本
REM 需要网络连接（CMake FetchContent 会拉取 nlohmann/json, miniz, pybind11）
setlocal
echo ==> 检查依赖...
where cmake >nul 2>nul
if %errorlevel% neq 0 (
    echo 请先安装 cmake
    exit /b 1
)
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo 请先安装 python3
    exit /b 1
)
echo ==> 安装 Python 依赖...
pip install -r frontend\requirements.txt
echo ==> 配置 CMake...
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
echo ==> 编译 C++ 后端 + pybind11 绑定...
cmake --build build --config Release --parallel
echo ==> 构建完成！运行方式：
echo     cd frontend ^&^& python main.py
pause
