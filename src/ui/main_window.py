from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QApplication,
)
from PySide6.QtGui import QFont

from src.ui.archive_tab import ArchiveTab
from src.ui.kindle_tab import KindleTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("漫画装订机")
        self.resize(920, 680)

        screen = QApplication.primaryScreen()
        if screen:
            center = screen.geometry().center()
            self.move(
                center.x() - self.width() // 2,
                center.y() - self.height() // 2,
            )

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

        self._tabs = QTabWidget()
        font = self._tabs.font()
        font.setPointSize(11)
        self._tabs.setFont(font)

        self._archive_tab = ArchiveTab()
        self._kindle_tab = KindleTab()

        self._tabs.addTab(self._archive_tab, "压缩包转PDF")
        self._tabs.addTab(self._kindle_tab, "Kindle漫画转换")

        layout.addWidget(self._tabs)
