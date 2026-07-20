# SilkModHub · 丝之歌 Mod 管理器

一个为《空洞骑士：丝之歌》(Hollow Knight: Silksong) 打造的桌面 Mod 管理器。

- **前端**：Python 3.12
- **后端**：C++17
- **容错设计**：即使没有编译 C++ 后端，前端也能用内置的纯 Python 实现完整运行
  （功能一致，仅性能略低），方便快速试用和界面调试

---

## 功能

- 🧵 **雷霆商店浏览**：一键拉取 `thunderstore.io/c/<community>` 社区的模组列表
- 📦 **本地模组管理**：安装、卸载、启用/禁用（禁用采用重命名 `.disabled` 后缀的方式，
  不删除文件，可随时恢复）
- 🎮 **游戏路径自动检测**：自动扫描 Steam 库（含 `libraryfolders.vdf` 自定义库路径）、
  GOG 常见路径；也可在设置中手动指定
- ⬇ **异步下载安装**：下载与解压在后台线程执行，带实时进度条

---

## 快速开始

### 方式一：只运行前端（纯 Python 回退实现，无需编译 C++）

```bash
cd frontend
pip install -r requirements.txt
python3 main.py
```

此时雷霆商店拉取、模组安装等功能均由内置的纯 Python 实现完成（依赖 `requests`），
无需任何 C++ 编译步骤，适合快速体验界面或做前端开发调试。

### 方式二：完整构建（启用高性能 C++ 后端）

**依赖**：CMake ≥ 3.16、支持 C++17 的编译器、libcurl 开发包、Python 3.9+、网络连接
（用于 CMake FetchContent 拉取 nlohmann/json、miniz、pybind11 源码）

```bash
# 可选：先运行依赖检测脚本，获取你所在系统的具体安装命令
python3 scripts/install_dependencies.py

# 一键构建（会自动安装 Python 依赖、配置并编译 C++ 后端）
chmod +x build.sh
./build.sh

# 构建完成后运行
cd frontend
python3 main.py
```

编译产物 `silk_backend.*.so`（Linux/macOS）或 `silk_backend.*.pyd`（Windows）会自动
输出到 `frontend/` 目录下，`main.py` 启动时会优先 `import silk_backend`，成功则自动
切换为 C++ 实现，无需修改任何代码。

### 独立测试后端（不启动 GUI）

```bash
# C++ CLI（编译后位于 build/backend/silk_backend_cli）
./build/backend/silk_backend_cli detect   # 检测游戏路径
./build/backend/silk_backend_cli fetch    # 拉取雷霆商店模组列表
./build/backend/silk_backend_cli list     # 列出已安装模组

# 或者用 Python 脚本快速测试游戏检测逻辑
python3 scripts/detect_game.py
```

---

## 关于雷霆商店社区标识

代码中默认使用的社区标识是 `hollow-knight-silksong`（对应 `https://thunderstore.io/c/hollow-knight-silksong/`）。
如果该社区的实际名称有变化，可以在应用内「设置」→「雷霆商店社区」中修改，
无需重新编译。

## 关于游戏 AppID / 可执行文件名

`GameDetector` 中的 Steam AppID 和可执行文件名目前是按官方公开信息填写的占位值，
如果检测不到，可在「设置」中点击「浏览…」手动选择游戏安装目录，程序会自动校验。

---

## 许可证

本项目为示例工程，可自由修改和使用。《空洞骑士：丝之歌》为 Team Cherry 所有，
本工具与 Team Cherry、雷霆商店 (Thunderstore) 无官方关联。
