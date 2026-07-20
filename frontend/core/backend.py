"""
core/backend.py
统一的后端访问层。

优先尝试导入编译好的 C++ 扩展模块 `silk_backend`（通过 pybind11 生成）。
如果尚未编译（例如纯前端界面开发调试阶段），则自动回退到一套功能等价的
纯 Python 实现，保证 GUI 在任何环境下都能启动和演示。
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

try:
    import silk_backend as _native                       
    NATIVE_AVAILABLE = True
except ImportError:
    _native = None
    NATIVE_AVAILABLE = False

import requests

from core.config import DATA_DIR as APP_DATA_DIR


                                                                               
                                     
                                                                               

@dataclass
class GameInstall:
    path: str = ""
    executable: str = ""
    source: str = ""
    valid: bool = False


@dataclass
class TSPackage:
    uuid: str
    name: str
    owner: str
    description: str
    icon_url: str
    website_url: str
    categories: List[str]
    dependencies: List[str]
    downloads: int
    likes: int
    is_pinned: bool
    is_deprecated: bool
    date_updated: str
    version_number: str
    download_url: str
    file_size: int


@dataclass
class InstalledMod:
    uuid: str
    name: str
    author: str
    version: str
    description: str
    install_path: str
    enabled: bool = True


@dataclass
class AppConfig:
    game_path: str = ""
    theme: str = "silk"
    community: str = "hollow-knight-silksong"
    check_updates_on_start: bool = True
    language: str = "zh_CN"


CONFIG_PATH = APP_DATA_DIR / "config.json"


                                                                               
                               
                                                                               

class _PyGameDetector:
    EXE_NAMES = {
        "Windows": "Hollow Knight Silksong.exe",
        "Darwin": "Hollow Knight Silksong.app",
        "Linux": "Hollow Knight Silksong.x86_64",
    }

    def _exe_name(self) -> str:
        return self.EXE_NAMES.get(platform.system(), self.EXE_NAMES["Linux"])

    def _looks_valid(self, path: str) -> bool:
        p = Path(path)
        return p.is_dir() and (p / self._exe_name()).exists()

    def _steam_libraries(self) -> List[Path]:
        libs: List[Path] = []
        system = platform.system()
        candidates: List[Path] = []
        if system == "Windows":
            for env in ("ProgramFiles(x86)", "ProgramFiles"):
                base = os.environ.get(env)
                if base:
                    candidates.append(Path(base) / "Steam")
        elif system == "Darwin":
            home = os.environ.get("HOME")
            if home:
                candidates.append(Path(home) / "Library/Application Support/Steam")
        else:
            home = os.environ.get("HOME")
            if home:
                candidates += [
                    Path(home) / ".steam/steam",
                    Path(home) / ".local/share/Steam",
                    Path(home) / ".var/app/com.valvesoftware.Steam/data/Steam",
                ]

        for base in candidates:
            common = base / "steamapps" / "common"
            if common.exists():
                libs.append(common)
            vdf = base / "steamapps" / "libraryfolders.vdf"
            if vdf.exists():
                try:
                    text = vdf.read_text(errors="ignore")
                    for line in text.splitlines():
                        if '"path"' in line:
                            parts = line.split('"')
                                                             
                            if len(parts) >= 4:
                                lib_path = parts[3].replace("\\\\", "\\")
                                p = Path(lib_path) / "steamapps" / "common"
                                if p.exists():
                                    libs.append(p)
                except OSError:
                    pass
        return libs

    def detect(self) -> Optional[GameInstall]:
        for lib in self._steam_libraries():
            try:
                for entry in lib.iterdir():
                    if entry.is_dir() and "silksong" in entry.name.lower():
                        if self._looks_valid(str(entry)):
                            return GameInstall(
                                path=str(entry),
                                executable=str(entry / self._exe_name()),
                                source="steam",
                                valid=True,
                            )
            except OSError:
                continue
        return None

    def validate_manual_path(self, path: str) -> GameInstall:
        valid = self._looks_valid(path)
        return GameInstall(
            path=path,
            executable=str(Path(path) / self._exe_name()) if valid else "",
            source="manual",
            valid=valid,
        )

    def get_mods_directory(self, install: GameInstall) -> str:
                                               
                                                       
        mods_dir = Path(install.path) / "BepInEx" / "plugins"
        mods_dir.mkdir(parents=True, exist_ok=True)
        return str(mods_dir)


class _PyModManager:
    def __init__(self, game_mods_dir: str, data_dir: str):
        self.game_mods_dir = Path(game_mods_dir)
        self.data_dir = Path(data_dir)
        self.game_mods_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._mods: List[InstalledMod] = []

    def _manifest_path(self) -> Path:
        return self.data_dir / "mods.json"

    def load_local_manifest(self):
        self._mods.clear()
        p = self._manifest_path()
        if not p.exists():
            return
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            for item in data:
                self._mods.append(InstalledMod(**item))
        except (json.JSONDecodeError, TypeError, OSError):
            pass

    def save_local_manifest(self):
        data = [m.__dict__ for m in self._mods]
        self._manifest_path().write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")

    def installed_mods(self) -> List[InstalledMod]:
        return self._mods

                                           
    _LANG_DIR_KEYWORDS = ("lang", "language", "languages", "i18n", "locale", "locales", "translation", "translations")

    @classmethod
    def _should_extract(cls, member_name: str) -> bool:
        """只保留 .dll 文件本身，以及语言/本地化文件夹下的所有文件；
        跳过 manifest.json / README.md / icon.png / CHANGELOG.md 等
        Thunderstore 打包时附带、BepInEx 运行不需要的说明性文件。"""
        parts = [p.lower() for p in Path(member_name).parts]
        if not parts:
            return False
        if parts[-1].endswith(".dll"):
            return True
        return any(part in cls._LANG_DIR_KEYWORDS for part in parts[:-1])

    @classmethod
    def _dest_relpath(cls, member_name: str) -> Path:
        """算出解压目标相对路径：把包内部自带的命名空间/`plugins`等嵌套目录
        拍平掉，最终效果是 BepInEx/plugins/<mod>/*.dll 直接落地，不是
        BepInEx/plugins/<mod>/hk-speedrunning/plugins/*.dll 这种嵌套。
        语言文件夹保留其自身目录名（从匹配到的那一级开始），但同样去掉
        更外层的嵌套路径。"""
        parts = Path(member_name).parts
        fname = parts[-1]
        if fname.lower().endswith(".dll"):
            return Path(fname)
        for idx, part in enumerate(parts[:-1]):
            if part.lower() in cls._LANG_DIR_KEYWORDS:
                return Path(*parts[idx:])
        return Path(fname)

    def install_from_zip(self, zip_path, uuid, name, author, version, description,
                          on_progress: Optional[Callable[[int, int, str], None]] = None) -> bool:
        try:
            if on_progress:
                on_progress(0, 100, "正在解压模组文件")
            dest_dir = self.game_mods_dir / uuid
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            dest_dir.mkdir(parents=True)

            with zipfile.ZipFile(zip_path) as zf:
                members = [m for m in zf.infolist()
                           if not m.is_dir() and self._should_extract(m.filename)]
                seen_dll_names = set()
                for member in members:
                    rel_path = self._dest_relpath(member.filename)
                    if rel_path.suffix.lower() == ".dll":
                                                     
                                               
                        key = rel_path.name.lower()
                        if key in seen_dll_names:
                            continue
                        seen_dll_names.add(key)
                    target = dest_dir / rel_path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)

            if not any(dest_dir.glob("*.dll")):
                                                     
                                                 
                shutil.rmtree(dest_dir, ignore_errors=True)
                if on_progress:
                    on_progress(0, 100, "安装失败：压缩包内未找到 .dll 文件")
                return False

            if on_progress:
                on_progress(90, 100, "正在登记模组信息")

            existing = next((m for m in self._mods if m.uuid == uuid), None)
            mod = InstalledMod(uuid=uuid, name=name, author=author, version=version,
                                description=description, install_path=str(dest_dir), enabled=True)
            if existing:
                idx = self._mods.index(existing)
                self._mods[idx] = mod
            else:
                self._mods.append(mod)
            self.save_local_manifest()

            if on_progress:
                on_progress(100, 100, "安装完成")
            return True
        except (OSError, zipfile.BadZipFile):
            if on_progress:
                on_progress(0, 100, "安装失败")
            return False

    def uninstall(self, uuid: str) -> bool:
        mod = next((m for m in self._mods if m.uuid == uuid), None)
        if not mod:
            return False
        shutil.rmtree(mod.install_path, ignore_errors=True)
        shutil.rmtree(mod.install_path + ".disabled", ignore_errors=True)
        self._mods.remove(mod)
        self.save_local_manifest()
        return True

    def set_enabled(self, uuid: str, enabled: bool) -> bool:
        mod = next((m for m in self._mods if m.uuid == uuid), None)
        if not mod or mod.enabled == enabled:
            return mod is not None
        src = Path(mod.install_path if enabled else mod.install_path)
        disabled_path = mod.install_path + ".disabled"
        try:
            if enabled and Path(disabled_path).exists():
                os.rename(disabled_path, mod.install_path)
            elif not enabled and Path(mod.install_path).exists():
                os.rename(mod.install_path, disabled_path)
            mod.enabled = enabled
            self.save_local_manifest()
            return True
        except OSError:
            return False

    def is_installed(self, uuid: str) -> bool:
        return any(m.uuid == uuid for m in self._mods)

    def installed_version(self, uuid: str) -> str:
        mod = next((m for m in self._mods if m.uuid == uuid), None)
        return mod.version if mod else ""


class _PyThunderstoreClient:
    def __init__(self, community: str = "hollow-knight-silksong"):
        self.community = community

    def set_community(self, community: str):
        self.community = community

    def _api_url(self) -> str:
        return f"https://thunderstore.io/c/{self.community}/api/v1/package/"

    def fetch_package_list(self):
        try:
            resp = requests.get(self._api_url(), timeout=30,
                                 headers={"User-Agent": "SilkModHub/1.0"})
            resp.raise_for_status()
            raw = resp.json()
        except requests.RequestException as e:
            return False, f"网络请求失败: {e}", []
        except ValueError as e:
            return False, f"解析雷霆商店数据失败: {e}", []

        packages: List[TSPackage] = []
        for item in raw:
            versions = item.get("versions") or []
            latest = versions[0] if versions else {}
            packages.append(TSPackage(
                uuid=item.get("full_name", ""),
                name=item.get("name", ""),
                owner=item.get("owner", ""),
                description=latest.get("description", ""),
                icon_url=latest.get("icon", ""),
                website_url=latest.get("website_url", ""),
                categories=item.get("categories", []) or [],
                dependencies=latest.get("dependencies", []) or [],
                downloads=latest.get("downloads", 0),
                likes=item.get("rating_score", 0),
                is_pinned=item.get("is_pinned", False),
                is_deprecated=item.get("is_deprecated", False),
                date_updated=item.get("date_updated", ""),
                version_number=latest.get("version_number", ""),
                download_url=latest.get("download_url", ""),
                file_size=latest.get("file_size", 0),
            ))
        return True, "", packages

    @staticmethod
    def filter(all_packages: List[TSPackage], keyword: str, category: str = "") -> List[TSPackage]:
        kw = keyword.lower()
        out = []
        for p in all_packages:
            if category and category not in p.categories:
                continue
            if kw and kw not in p.name.lower() and kw not in p.owner.lower() and kw not in p.description.lower():
                continue
            out.append(p)
        return out

    def download_file(self, url: str, dest_path: str,
                       on_progress: Optional[Callable[[int, int], None]] = None) -> bool:
        try:
            with requests.get(url, stream=True, timeout=300) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                done = 0
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        f.write(chunk)
                        done += len(chunk)
                        if on_progress:
                            on_progress(done, total)
            return True
        except (requests.RequestException, OSError):
            return False


                                                                               
                                                  
                                                                               

class Backend:
    """UI 层唯一需要接触的入口。屏蔽了 native/pure-python 差异。"""

    def __init__(self):
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.config = self.load_config()

        if NATIVE_AVAILABLE:
            self._detector = _native.GameDetector()
        else:
            self._detector = _PyGameDetector()

        self._mod_manager: Optional[object] = None
        self._thunderstore = (
            _native.ThunderstoreClient(self.config.community)
            if NATIVE_AVAILABLE else _PyThunderstoreClient(self.config.community)
        )

                                          
    def load_config(self) -> AppConfig:
        if not CONFIG_PATH.exists():
            return AppConfig()
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return AppConfig(**{**AppConfig().__dict__, **data})
        except (json.JSONDecodeError, OSError, TypeError):
            return AppConfig()

    def save_config(self):
        CONFIG_PATH.write_text(json.dumps(self.config.__dict__, ensure_ascii=False, indent=4),
                                encoding="utf-8")

                                            
    def detect_game(self) -> Optional[GameInstall]:
        result = self._detector.detect()
        if result is None:
            return None
        if NATIVE_AVAILABLE:
            return GameInstall(path=result.path, executable=result.executable,
                                source=result.source, valid=result.valid)
        return result

    def validate_manual_path(self, path: str) -> GameInstall:
        result = self._detector.validate_manual_path(path)
        if NATIVE_AVAILABLE:
            return GameInstall(path=result.path, executable=result.executable,
                                source=result.source, valid=result.valid)
        return result

    def ensure_mod_manager(self, game_path: str):
        if NATIVE_AVAILABLE:
            install = _native.GameInstall()
            install.path = game_path
            mods_dir = self._detector.get_mods_directory(install)
            self._mod_manager = _native.ModManager(mods_dir, str(APP_DATA_DIR))
        else:
            mods_dir = self._detector.get_mods_directory(GameInstall(path=game_path, valid=True))
            self._mod_manager = _PyModManager(mods_dir, str(APP_DATA_DIR))
        self._mod_manager.load_local_manifest()
        return self._mod_manager

    @property
    def mod_manager(self):
        if self._mod_manager is None:
            self.ensure_mod_manager(self.config.game_path)
        return self._mod_manager

                                            
    def fetch_thunderstore(self):
        self._thunderstore.set_community(self.config.community)
        if NATIVE_AVAILABLE:
            result = self._thunderstore.fetch_package_list()
            packages = [
                TSPackage(
                    uuid=p.uuid, name=p.name, owner=p.owner, description=p.description,
                    icon_url=p.icon_url, website_url=p.website_url, categories=list(p.categories),
                    dependencies=list(p.dependencies), downloads=p.downloads, likes=p.likes,
                    is_pinned=p.is_pinned, is_deprecated=p.is_deprecated, date_updated=p.date_updated,
                    version_number=p.latest.version_number, download_url=p.latest.download_url,
                    file_size=p.latest.file_size,
                ) for p in result.packages
            ] if result.success else []
            return result.success, result.error, packages
        return self._thunderstore.fetch_package_list()

    def download_and_install(self, package: TSPackage, tmp_dir: str,
                              on_progress: Optional[Callable[[int, int, str], None]] = None) -> bool:
        tmp_zip = str(Path(tmp_dir) / f"{package.uuid}.zip")

        def dl_progress(done, total):
            if on_progress:
                on_progress(done, total or 1, "正在下载")

        ok = self._thunderstore.download_file(package.download_url, tmp_zip, dl_progress)
        if not ok:
            return False

        return self.mod_manager.install_from_zip(
            tmp_zip, package.uuid, package.name, package.owner,
            package.version_number, package.description, on_progress,
        )
