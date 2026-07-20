"""
ui/settings_window.py
设置对话框。
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QFileDialog, QCheckBox, QMessageBox, QFormLayout,
)

from core.backend import Backend
from core.theme import THEME_LABELS, apply_theme
from ui.widgets import PillButton


class SettingsDialog(QDialog):
    def __init__(self, backend: Backend, parent=None):
        super().__init__(parent)
        self.backend = backend
        self.setWindowTitle("设置")
        self.setMinimumWidth(480)
        self.setObjectName("SettingsDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        title = QLabel("⚙  应用设置")
        title.setObjectName("DialogTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

              
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(backend.config.game_path)
        self.path_edit.setPlaceholderText("《空洞骑士：丝之歌》安装目录")
        browse_btn = QPushButton("浏览…")
        browse_btn.clicked.connect(self._browse_path)
        detect_btn = QPushButton("自动检测")
        detect_btn.clicked.connect(self._auto_detect)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_btn)
        path_row.addWidget(detect_btn)
        form.addRow("游戏目录", path_row)

                
        self.community_edit = QLineEdit(backend.config.community)
        self.community_edit.setPlaceholderText("例如: silksong")
        form.addRow("雷霆商店社区", self.community_edit)

            
        self.theme_combo = QComboBox()
        for key, label in THEME_LABELS.items():
            self.theme_combo.addItem(label, key)
        current_index = self.theme_combo.findData(backend.config.theme)
        if current_index >= 0:
            self.theme_combo.setCurrentIndex(current_index)
        form.addRow("界面主题", self.theme_combo)

                 
        self.check_updates_box = QCheckBox("启动时自动检查模组更新")
        self.check_updates_box.setChecked(backend.config.check_updates_on_start)
        form.addRow("", self.check_updates_box)

        layout.addLayout(form)

        self.status_label = QLabel("")
        self.status_label.setObjectName("SettingsStatus")
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        save_btn = PillButton("保存", accent=True)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择《丝之歌》安装目录")
        if path:
            self.path_edit.setText(path)

    def _auto_detect(self):
        install = self.backend.detect_game()
        if install and install.valid:
            self.path_edit.setText(install.path)
            self.status_label.setText(f"✅ 自动检测成功：{install.source}")
        else:
            self.status_label.setText("⚠ 未能自动检测到游戏，请手动选择目录")

    def _save(self):
        path = self.path_edit.text().strip()
        if path:
            install = self.backend.validate_manual_path(path)
            if not install.valid:
                reply = QMessageBox.question(
                    self, "路径校验失败",
                    "所选目录中未找到《丝之歌》可执行文件，是否仍然保存该路径？",
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

        cfg = self.backend.config
        cfg.game_path = path
        cfg.community = self.community_edit.text().strip() or "hollow-knight-silksong"
        cfg.theme = self.theme_combo.currentData()
        cfg.check_updates_on_start = self.check_updates_box.isChecked()
        self.backend.save_config()

        from PyQt6.QtWidgets import QApplication
        apply_theme(QApplication.instance(), cfg.theme)

        if path:
            self.backend.ensure_mod_manager(path)

        self.accept()
