"""
ui/main_window.py
应用主窗口。
"""
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QStackedWidget, QProgressBar,
    QSizePolicy, QFrame,
)

from core.backend import Backend, TSPackage
from core.config import APP_NAME, APP_SUBTITLE, APP_VERSION
from ui.widgets import FlowLayout, SearchBox, Toast, PillButton
from ui.mod_card import ModCard
from ui.settings_window import SettingsDialog


class FetchWorker(QThread):
    """在后台线程拉取雷霆商店模组列表，避免阻塞界面。"""
    done = pyqtSignal(bool, str, list)

    def __init__(self, backend: Backend):
        super().__init__()
        self.backend = backend

    def run(self):
        ok, err, packages = self.backend.fetch_thunderstore()
        self.done.emit(ok, err, packages)


class InstallWorker(QThread):
    """在后台线程下载并安装单个模组。"""
    progress = pyqtSignal(int, int, str)
    done = pyqtSignal(bool, str)

    def __init__(self, backend: Backend, package: TSPackage, tmp_dir: str):
        super().__init__()
        self.backend = backend
        self.package = package
        self.tmp_dir = tmp_dir

    def run(self):
        def on_progress(cur, total, stage):
            self.progress.emit(cur, total, stage)

        ok = self.backend.download_and_install(self.package, self.tmp_dir, on_progress)
        self.done.emit(ok, self.package.name)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.backend = Backend()
        self.all_packages: list[TSPackage] = []

        self._fetch_worker: FetchWorker | None = None
        self._install_worker: InstallWorker | None = None
        self._tmp_dir = tempfile.mkdtemp(prefix="silkmodhub_")

        self.setWindowTitle(f"{APP_NAME} · {APP_SUBTITLE}")
        self.resize(1180, 760)
        self.setMinimumSize(940, 600)

        self._build_ui()
        self._init_game_state()

                                                                          
          
                                                                          
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("RootBackground")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(24, 20, 24, 20)
        right_layout.setSpacing(16)

        right_layout.addWidget(self._build_topbar())
        right_layout.addWidget(self._build_status_banner())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_browse_page())
        self.stack.addWidget(self._build_installed_page())
        right_layout.addWidget(self.stack, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("InstallProgress")
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        right_layout.addWidget(self.progress_bar)

        root.addWidget(right, 1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 26, 20, 20)
        layout.setSpacing(6)

        brand = QLabel(f"🕸  {APP_NAME}")
        brand.setObjectName("BrandTitle")
        subtitle = QLabel(APP_SUBTITLE)
        subtitle.setObjectName("BrandSubtitle")
        layout.addWidget(brand)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        self.nav_browse = self._nav_button("🧵  浏览雷霆商店", checked=True)
        self.nav_installed = self._nav_button("📦  已安装模组")
        self.nav_browse.clicked.connect(lambda: self._switch_page(0))
        self.nav_installed.clicked.connect(lambda: self._switch_page(1))
        layout.addWidget(self.nav_browse)
        layout.addWidget(self.nav_installed)

        layout.addStretch(1)

        settings_btn = QPushButton("⚙  设置")
        settings_btn.setObjectName("SettingsButton")
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setObjectName("VersionLabel")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        return sidebar

    def _nav_button(self, text: str, checked: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _build_topbar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.search_box = SearchBox("搜索模组、作者或描述…")
        self.search_box.textChanged.connect(self._apply_filters)
        layout.addWidget(self.search_box, 1)

        refresh_btn = PillButton("刷新列表", accent=True)
        refresh_btn.clicked.connect(self._refresh_thunderstore)
        layout.addWidget(refresh_btn)

        return bar

    def _build_status_banner(self) -> QWidget:
        self.status_label = QLabel()
        self.status_label.setObjectName("StatusBanner")
        self.status_label.setWordWrap(True)
        return self.status_label

    def _build_browse_page(self) -> QWidget:
        page = QScrollArea()
        page.setWidgetResizable(True)
        page.setObjectName("ScrollArea")
        container = QWidget()
        self.browse_flow = FlowLayout(container, margin=4, h_spacing=16, v_spacing=16)
        page.setWidget(container)
        self.browse_placeholder = QLabel(
            "点击右上角「刷新列表」从雷霆商店获取《丝之歌》模组列表 🧵"
        )
        self.browse_placeholder.setObjectName("PlaceholderLabel")
        self.browse_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.browse_flow.addWidget(self.browse_placeholder)
        return page

    def _build_installed_page(self) -> QWidget:
        page = QScrollArea()
        page.setWidgetResizable(True)
        page.setObjectName("ScrollArea")
        container = QWidget()
        self.installed_flow = FlowLayout(container, margin=4, h_spacing=16, v_spacing=16)
        page.setWidget(container)
        return page

                                                                          
           
                                                                          
    def _init_game_state(self):
        cfg = self.backend.config
        install = None
        if cfg.game_path:
            install = self.backend.validate_manual_path(cfg.game_path)
        if not install or not install.valid:
            install = self.backend.detect_game()
            if install and install.valid:
                cfg.game_path = install.path
                self.backend.save_config()

        if install and install.valid:
            self.backend.ensure_mod_manager(install.path)
            self.status_label.setText(f"✅ 已定位游戏目录：{install.path}")
            self.status_label.setObjectName("StatusBannerOk")
            self._refresh_installed_page()
        else:
            self.status_label.setText("⚠ 未检测到游戏安装目录，请前往「设置」手动指定后再安装模组。")
            self.status_label.setObjectName("StatusBannerWarn")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.nav_browse.setChecked(index == 0)
        self.nav_installed.setChecked(index == 1)
        if index == 1:
            self._refresh_installed_page()

    def _open_settings(self):
        dlg = SettingsDialog(self.backend, self)
        if dlg.exec():
            self._init_game_state()

    def _refresh_thunderstore(self):
        self.status_label.setText(f"🔄 正在从雷霆商店拉取「{self.backend.config.community}」社区模组列表…")
        self._fetch_worker = FetchWorker(self.backend)
        self._fetch_worker.done.connect(self._on_fetch_done)
        self._fetch_worker.start()

    def _on_fetch_done(self, ok: bool, error: str, packages: list):
        if not ok:
            self.status_label.setText(f"❌ 获取失败：{error}")
            Toast(self, f"获取模组列表失败：{error}", kind="error")
            return
        self.all_packages = packages
        self.status_label.setText(f"✅ 共获取到 {len(packages)} 个模组，来自雷霆商店「{self.backend.config.community}」社区")
        self._apply_filters()

    def _apply_filters(self):
        keyword = self.search_box.text().strip()
        self._render_browse_cards(keyword)

    def _render_browse_cards(self, keyword: str):
               
        while self.browse_flow.count():
            item = self.browse_flow.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.all_packages:
            self.browse_flow.addWidget(self.browse_placeholder)
            return

        kw = keyword.lower()
        for pkg in self.all_packages:
            if kw and kw not in pkg.name.lower() and kw not in pkg.owner.lower()\
                    and kw not in pkg.description.lower():
                continue
            installed_version = ""
            try:
                installed_version = self.backend.mod_manager.installed_version(pkg.uuid)
            except Exception:
                pass
            card = ModCard("browse", pkg, installed_version=installed_version)
            card.install_requested.connect(self._on_install_requested)
            self.browse_flow.addWidget(card)

    def _refresh_installed_page(self):
        while self.installed_flow.count():
            item = self.installed_flow.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        try:
            mods = self.backend.mod_manager.installed_mods()
        except Exception:
            mods = []

        if not mods:
            empty = QLabel("暂无已安装模组，去「浏览雷霆商店」页面挑选一些吧～")
            empty.setObjectName("PlaceholderLabel")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.installed_flow.addWidget(empty)
            return

        for mod in mods:
            card = ModCard("installed", mod)
            card.uninstall_requested.connect(self._on_uninstall_requested)
            card.toggle_requested.connect(self._on_toggle_requested)
            self.installed_flow.addWidget(card)

                                                                          
                    
                                                                          
    def _on_install_requested(self, package: TSPackage):
        if not self.backend.config.game_path:
            Toast(self, "请先在「设置」中指定游戏安装目录", kind="error")
            return

        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.status_label.setText(f"⬇ 正在安装「{package.name}」…")

        self._install_worker = InstallWorker(self.backend, package, self._tmp_dir)
        self._install_worker.progress.connect(self._on_install_progress)
        self._install_worker.done.connect(self._on_install_done)
        self._install_worker.start()

    def _on_install_progress(self, current: int, total: int, stage: str):
        pct = int(current * 100 / total) if total else 0
        self.progress_bar.setValue(min(pct, 100))
        self.status_label.setText(f"⬇ {stage}… {pct}%")

    def _on_install_done(self, ok: bool, name: str):
        self.progress_bar.hide()
        if ok:
            self.status_label.setText(f"✅ 「{name}」安装完成")
            Toast(self, f"「{name}」安装成功", kind="success")
        else:
            self.status_label.setText(f"❌ 「{name}」安装失败")
            Toast(self, f"「{name}」安装失败，请检查网络或游戏路径", kind="error")
        self._apply_filters()
        self._refresh_installed_page()

    def _on_uninstall_requested(self, uuid: str):
        ok = self.backend.mod_manager.uninstall(uuid)
        Toast(self, "模组已卸载" if ok else "卸载失败", kind="success" if ok else "error")
        self._refresh_installed_page()
        self._apply_filters()

    def _on_toggle_requested(self, uuid: str, enabled: bool):
        ok = self.backend.mod_manager.set_enabled(uuid, enabled)
        if not ok:
            Toast(self, "切换启用状态失败", kind="error")
            self._refresh_installed_page()

    def closeEvent(self, event):
        self.backend.save_config()
        super().closeEvent(event)
