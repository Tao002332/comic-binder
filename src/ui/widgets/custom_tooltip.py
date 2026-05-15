from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QPoint, QObject, QEvent
from PySide6.QtWidgets import QLabel, QWidget
from PySide6.QtGui import QPalette, QColor


class TipLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAutoFillBackground(True)

        p = self.palette()
        p.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        p.setColor(QPalette.ColorRole.WindowText, QColor("#1c1c1e"))
        self.setPalette(p)

        self.setStyleSheet("""
            TipLabel {
                background-color: #ffffff;
                color: #1c1c1e;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 13px;
            }
        """)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_text(self, text: str, widget: QWidget = None):
        self.setText(text)
        self.adjustSize()
        if widget:
            pos = widget.mapToGlobal(QPoint(12, -self.height() - 4))
            self.move(pos)
        self.show()
        self.raise_()
        self._timer.start(5000)


_global_tip = None


def _get_tip() -> TipLabel:
    global _global_tip
    if _global_tip is None:
        _global_tip = TipLabel()
    return _global_tip


class HoverTip(QObject):
    """Install on any QWidget to show a styled tooltip on hover."""

    def __init__(self, widget: QWidget, text: str):
        super().__init__(widget)
        self._widget = widget
        self._text = text
        widget.installEventFilter(self)
        widget.setToolTip("")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            tip = _get_tip()
            tip.show_text(self._text, self._widget)
        elif event.type() == QEvent.Type.Leave:
            _get_tip().hide()
        return False


def install(widget: QWidget, text: str):
    """Attach styled tooltip to a widget."""
    HoverTip(widget, str(text))
