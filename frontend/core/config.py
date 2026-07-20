"""
core/config.py
应用级静态常量：路径、版本号、雷霆商店社区标识等。
运行期可变配置（主题选择、游戏路径等）由 core/backend.py 中的 AppConfig 负责。
"""
import sys
import os
from pathlib import Path

APP_NAME = "SilkModHub"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "丝之歌 Mod 管理器"

                                                     
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
                                                
                                                    
    FRONTEND_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    PROJECT_ROOT = FRONTEND_DIR
    THEMES_DIR = FRONTEND_DIR / "themes"
    ASSETS_DIR = FRONTEND_DIR / "assets"
                                                     
    if sys.platform == "darwin":
        DATA_DIR = Path.home() / "Library" / "Application Support" / APP_NAME
    elif sys.platform == "win32":
        DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
    else:
        DATA_DIR = Path.home() / ".config" / APP_NAME
else:
    FRONTEND_DIR = Path(__file__).resolve().parent.parent
    PROJECT_ROOT = FRONTEND_DIR.parent
    THEMES_DIR = FRONTEND_DIR / "themes"
    ASSETS_DIR = FRONTEND_DIR / "assets"
    DATA_DIR = PROJECT_ROOT / "data"

DEFAULT_COMMUNITY = "hollow-knight-silksong"
THUNDERSTORE_BASE = "https://thunderstore.io"

                    
MOD_CATEGORIES = [
    ("全部", ""),
    ("游戏内容", "content"),
    ("Boss / 敌人", "bosses"),
    ("UI 界面", "ui"),
    ("辅助工具", "tools"),
    ("翻译 / 本地化", "translation"),
    ("音乐 / 美术", "audio-visual"),
    ("依赖库", "libraries"),
]

DATA_DIR.mkdir(parents=True, exist_ok=True)
