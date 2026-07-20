"""
ui/widgets.py
一些可在多处复用的自定义控件。
"""
from PyQt6.QtCore import Qt, QRect, QSize, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QLayout, QLayoutItem, QSizePolicy, QLineEdit, QLabel,
    QHBoxLayout, QVBoxLayout, QFrame, QGraphicsOpacityEffect, QPushButton,
)


class FlowLayout(QLayout):
    """经典的 Qt 流式布局实现：子控件在宽度不足时自动换行，用于模组卡片网格。"""

    def __init__(self, parent=None, margin: int = 0, h_spacing: int = 14, v_spacing: int = 14):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def horizontalSpacing(self):
        return self._h_spacing

    def verticalSpacing(self):
        return self._v_spacing

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x, y = effective_rect.x(), effective_rect.y()
        line_height = 0

        for item in self._items:
            widget = item.widget()
            space_x = self._h_spacing
            space_y = self._v_spacing
            next_x = x + item.sizeHint().width() + space_x

            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + bottom


class SearchBox(QLineEdit):
    """带放大镜图标提示文字的搜索输入框。"""

    def __init__(self, placeholder: str = "搜索模组、作者或描述…", parent=None):
        super().__init__(parent)
        self.setObjectName("SearchBox")
        self.setPlaceholderText(f"🔍  {placeholder}")
        self.setClearButtonEnabled(True)
        self.setMinimumHeight(38)


class Toast(QFrame):
    """右下角短暂出现的提示气泡，用于安装成功/失败等反馈。"""

    def __init__(self, parent: QWidget, message: str, kind: str = "info", duration_ms: int = 2600):
        super().__init__(parent)
        self.setObjectName(f"Toast_{kind}")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        icon = {"success": "✓", "error": "✕", "info": "ℹ"}.get(kind, "ℹ")
        label = QLabel(f"{icon}  {message}")
        label.setObjectName("ToastLabel")
        layout.addWidget(label)

        self.adjustSize()
        self._reposition()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)
        self.show()
        self._fade_in()

        QTimer.singleShot(duration_ms, self._fade_out)

    def _reposition(self):
        parent_rect = self.parent().rect()
        margin = 24
        self.move(parent_rect.width() - self.width() - margin,
                  parent_rect.height() - self.height() - margin)

    def _fade_in(self):
        self._animate(0.0, 1.0)

    def _fade_out(self):
        self._animate(1.0, 0.0, on_finished=self.deleteLater)

    def _animate(self, start, end, on_finished=None):
        from PyQt6.QtCore import QPropertyAnimation
        anim = QPropertyAnimation(self._opacity, b"opacity", self)
        anim.setDuration(220)
        anim.setStartValue(start)
        anim.setEndValue(end)
        if on_finished:
            anim.finished.connect(on_finished)
        anim.start()
        self._anim = anim           


class PillButton(QPushButton):
    """圆角胶囊按钮，用于主要操作（安装/启用等）。"""

    def __init__(self, text: str, accent: bool = False, parent=None):
        super().__init__(text, parent)
        self.setObjectName("PillButtonAccent" if accent else "PillButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(32)
