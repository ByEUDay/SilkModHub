"""
ui/mod_card.py
展示单个模组的卡片控件，同时用于「雷霆商店浏览」和「已安装模组」两种场景。
"""
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QCheckBox,
)
from PyQt6 import sip

from ui.widgets import PillButton

CARD_WIDTH = 300
ICON_SIZE = 56

_network_manager: "QNetworkAccessManager | None" = None


def _get_network_manager() -> QNetworkAccessManager:
    """惰性创建全局共享的 QNetworkAccessManager。

    不能在模块导入时直接实例化：本模块会在 `QApplication` 创建之前被
    import（main.py 里先 import 各个 ui 模块，之后才 `QApplication(sys.argv)`），
    此时构造 QNetworkAccessManager 这类 QObject 是未定义行为，会触发
    `QObject::connect(...): invalid nullptr parameter` 警告。改成首次用到
    （即真正要下载图标、此时窗口早已创建完毕）时才创建，就不会有这个问题。
    """
    global _network_manager
    if _network_manager is None:
        _network_manager = QNetworkAccessManager()
    return _network_manager


class ModCard(QFrame):
    """一张模组卡片。

    mode="browse": 展示来自雷霆商店的数据，提供“安装/更新”按钮
    mode="installed": 展示本地已安装模组，提供“启用”开关与“卸载”按钮
    """

    install_requested = pyqtSignal(object)                   
    uninstall_requested = pyqtSignal(str)                
    toggle_requested = pyqtSignal(str, bool)                   

    def __init__(self, mode: str, data, installed_version: str = "", parent=None):
        super().__init__(parent)
        self.mode = mode
        self.data = data
        self.setObjectName("ModCard")
        self.setFixedWidth(CARD_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 14)
        outer.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(12)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("ModIcon")
        self.icon_label.setFixedSize(ICON_SIZE, ICON_SIZE)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setText("🕷")
        header.addWidget(self.icon_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        name = getattr(data, "name", "")
        owner = getattr(data, "owner", None) or getattr(data, "author", "")
        name_label = QLabel(name)
        name_label.setObjectName("ModName")
        name_label.setWordWrap(True)
        author_label = QLabel(f"by {owner}")
        author_label.setObjectName("ModAuthor")
        title_box.addWidget(name_label)
        title_box.addWidget(author_label)
        header.addLayout(title_box, 1)

        outer.addLayout(header)

        desc = getattr(data, "description", "") or "（作者未提供描述）"
        if len(desc) > 110:
            desc = desc[:110].rstrip() + "…"
        desc_label = QLabel(desc)
        desc_label.setObjectName("ModDesc")
        desc_label.setWordWrap(True)
        desc_label.setMinimumHeight(48)
        outer.addWidget(desc_label)

        meta = QHBoxLayout()
        if mode == "browse":
            downloads = getattr(data, "downloads", 0)
            version = getattr(data, "version_number", "")
            meta_label = QLabel(f"⬇ {self._format_count(downloads)}   v{version}")
        else:
            version = getattr(data, "version", "")
            meta_label = QLabel(f"版本 v{version}")
        meta_label.setObjectName("ModMeta")
        meta.addWidget(meta_label)
        meta.addStretch(1)
        outer.addLayout(meta)

        footer = QHBoxLayout()
        footer.setSpacing(10)

        if mode == "browse":
            installed = bool(installed_version)
            is_update = installed and installed_version != getattr(data, "version_number", "")
            if is_update:
                btn = PillButton("更新", accent=True)
            elif installed:
                btn = PillButton("已安装")
                btn.setEnabled(False)
            else:
                btn = PillButton("安装", accent=True)
            btn.clicked.connect(lambda: self.install_requested.emit(self.data))
            footer.addStretch(1)
            footer.addWidget(btn)
        else:
            self.toggle = QCheckBox("启用")
            self.toggle.setChecked(getattr(data, "enabled", True))
            self.toggle.toggled.connect(
                lambda checked: self.toggle_requested.emit(data.uuid, checked)
            )
            footer.addWidget(self.toggle)
            footer.addStretch(1)
            uninstall_btn = PillButton("卸载")
            uninstall_btn.clicked.connect(lambda: self.uninstall_requested.emit(data.uuid))
            footer.addWidget(uninstall_btn)

        outer.addLayout(footer)

        icon_url = getattr(data, "icon_url", "")
        if icon_url:
            self._load_icon(icon_url)

    @staticmethod
    def _format_count(n: int) -> str:
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)

    def _load_icon(self, url: str):
        request = QNetworkRequest(QUrl(url))
        reply = _get_network_manager().get(request)
        self._icon_reply = reply
        reply.finished.connect(lambda: self._on_icon_loaded(reply))
                                           
                                                  
        self.destroyed.connect(lambda: self._abort_icon_reply(reply))

    @staticmethod
    def _abort_icon_reply(reply):
        try:
            if not sip.isdeleted(reply):
                reply.abort()
        except Exception:
            pass

    def _on_icon_loaded(self, reply):
        data = reply.readAll()
        reply.deleteLater()
        try:
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                scaled = pixmap.scaled(ICON_SIZE, ICON_SIZE, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
                self.icon_label.setPixmap(scaled)
                self.icon_label.setText("")
        except RuntimeError:
                                                
                                                 
            pass
