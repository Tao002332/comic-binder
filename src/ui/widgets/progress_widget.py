from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QProgressBar, QLabel,
    QFrame, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView,
)

from src.core.task_manager import TaskItem, TaskStatus
from src.utils.comic_grouper import extract_comic_name
from src.ui.widgets.custom_tooltip import _get_tip


class ProgressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Overall card
        ov = QFrame()
        ov.setObjectName("glassOverall")
        ov.setStyleSheet("QFrame#glassOverall { background: rgba(255,255,255,0.72); border: 0.5px solid rgba(0,0,0,0.06); border-radius: 16px; }")
        ovl = QHBoxLayout(ov)
        ovl.setContentsMargins(16, 12, 16, 12)
        ovl.setSpacing(12)

        ot = QLabel("总体进度")
        ot.setStyleSheet("font-size: 14px; font-weight: 590; color: #1c1c1e; background: transparent; border: none;")
        ovl.addWidget(ot)

        self._overall_bar = QProgressBar()
        self._overall_bar.setRange(0, 100)
        self._overall_bar.setFixedHeight(6)
        self._overall_bar.setTextVisible(False)
        self._overall_bar.setStyleSheet("QProgressBar { border: none; border-radius: 3px; background: rgba(0,0,0,0.06); } QProgressBar::chunk { border-radius: 3px; background: #007aff; }")
        ovl.addWidget(self._overall_bar, stretch=1)

        self._overall_lbl = QLabel("就绪")
        self._overall_lbl.setStyleSheet("font-size: 12px; color: #8e8e93; background: transparent;")
        ovl.addWidget(self._overall_lbl)
        layout.addWidget(ov)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["文件名", "漫画名", "状态", "错误原因", "进度"])
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(True)
        self._table.setMouseTracking(True)
        self._table.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 72)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(4, 140)
        hh.setFixedHeight(32)
        hh.setStyleSheet("""
            QHeaderView::section {
                background: rgba(0,0,0,0.03); color: #8e8e93; padding: 6px 8px;
                border: none; border-bottom: 1px solid rgba(0,0,0,0.06); font-size: 11px; font-weight: 600;
            }
        """)
        self._table.setStyleSheet("""
            QTableWidget { border: none; background: transparent; gridline-color: rgba(0,0,0,0.04); }
            QTableWidget::item { padding: 8px 8px; font-size: 13px; color: #3c3c43; background: transparent; }
        """)
        layout.addWidget(self._table, stretch=1)

        self._table.cellEntered.connect(self._on_cell_hover)
        self._table.viewport().installEventFilter(self)
        self._tasks: dict[str, TaskItem] = {}
        self._resort_timer = QTimer(self)
        self._resort_timer.setSingleShot(True)
        self._resort_timer.setInterval(300)
        self._resort_timer.timeout.connect(self._rebuild)

    def register_task(self, tid: str, name: str):
        comic = extract_comic_name(name)
        item = TaskItem(task_id=tid, name=name, metadata={"comic": comic})
        self._tasks[tid] = item
        self._resort_timer.start()

    def update_task(self, task: TaskItem):
        existing = self._tasks.get(task.task_id)
        if existing:
            existing.status = task.status
            existing.progress = task.progress
            existing.status_text = task.status_text
            existing.error_message = task.error_message
        self._resort_timer.start()
        self._recalc()

    def _rebuild(self):
        self.setUpdatesEnabled(False)
        items = sorted(self._tasks.values(), key=lambda t: (
            t.metadata.get("comic", "").lower(),
            {"running": 0, "pending": 1, "done": 2, "error": 3}.get(t.status.value, 9),
            -t.progress
        ))
        self._table.setRowCount(0)
        for row, item in enumerate(items):
            self._table.insertRow(row)
            self._table.setRowHeight(row, 38)

            t0 = QTableWidgetItem(item.name)
            t0.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self._table.setItem(row, 0, t0)

            comic = item.metadata.get("comic", "")
            t1 = QTableWidgetItem(comic)
            t1.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self._table.setItem(row, 1, t1)

            labels = {"pending": "等待中", "running": "处理中", "done": "已完成", "error": "失败"}
            st = item.status.value
            t2 = QTableWidgetItem(labels.get(st, st))
            t2.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            if st == "done":
                t2.setForeground(Qt.GlobalColor.darkGreen)
            elif st == "error":
                t2.setForeground(Qt.GlobalColor.red)
            elif st == "running":
                t2.setForeground(Qt.GlobalColor.blue)
            self._table.setItem(row, 2, t2)

            t3 = QTableWidgetItem(item.error_message if st == "error" else "")
            t3.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            if st == "error":
                t3.setForeground(Qt.GlobalColor.red)
            self._table.setItem(row, 3, t3)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(item.progress)
            bar.setTextVisible(True)
            bar.setFixedHeight(18)
            if st == "done":
                bar.setStyleSheet("QProgressBar { border: none; border-radius: 4px; background: #e8f5e9; font-size: 10px; color: #1b5e20; } QProgressBar::chunk { border-radius: 4px; background: #43a047; }")
            elif st == "error":
                bar.setStyleSheet("QProgressBar { border: none; border-radius: 4px; background: #fce8e6; font-size: 10px; color: #1c1c1e; } QProgressBar::chunk { border-radius: 4px; background: #e53935; }")
            elif st == "running":
                bar.setStyleSheet("QProgressBar { border: none; border-radius: 4px; background: #e3f2fd; font-size: 10px; color: #1c1c1e; } QProgressBar::chunk { border-radius: 4px; background: #007aff; }")
            else:
                bar.setStyleSheet("QProgressBar { border: none; border-radius: 4px; background: #f5f5f5; font-size: 10px; color: #9e9e9e; } QProgressBar::chunk { border-radius: 4px; background: #bdbdbd; }")
            self._table.setCellWidget(row, 4, bar)

        self.setUpdatesEnabled(True)

    def _recalc(self):
        if not self._tasks:
            self._overall_bar.setValue(0)
            self._overall_lbl.setText("就绪")
            return
        vals = [t.progress for t in self._tasks.values()]
        self._overall_bar.setValue(sum(vals) // len(vals))
        done = sum(1 for t in self._tasks.values() if t.status == TaskStatus.DONE)
        err = sum(1 for t in self._tasks.values() if t.status == TaskStatus.ERROR)
        run = len(vals) - done - err
        parts = []
        if run: parts.append(f"{run} 处理中")
        if done: parts.append(f"{done} 完成")
        if err: parts.append(f"{err} 失败")
        self._overall_lbl.setText(", ".join(parts) if parts else "空闲")

    def clear(self):
        self._tasks.clear()
        self._table.setRowCount(0)
        self._overall_bar.setValue(0)
        self._overall_lbl.setText("就绪")

    def _on_cell_hover(self, row: int, col: int):
        if row < 0:
            _get_tip().hide()
            return
        item = self._table.item(row, col)
        if item and item.text():
            text = item.text()
            fm = self._table.fontMetrics()
            col_w = self._table.columnWidth(col)
            if fm.horizontalAdvance(text) > col_w - 16:
                rect = self._table.visualItemRect(item)
                pos = self._table.viewport().mapToGlobal(rect.topLeft())
                pos.setY(pos.y() - _get_tip().height() - 4)
                _get_tip().show_text(text, None)
                _get_tip().move(pos)
        else:
            _get_tip().hide()

    def eventFilter(self, obj, event):
        if obj is self._table.viewport() and event.type() == QEvent.Type.Leave:
            _get_tip().hide()
        return False

    def get_failed_tasks(self) -> list[TaskItem]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.ERROR]
