from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QProgressBar, QLabel,
    QFrame, QHBoxLayout, QCheckBox, QPushButton,
)

from src.core.task_manager import TaskItem, TaskStatus
from src.utils.comic_grouper import extract_comic_name


class _GlassProgressPanel(QFrame):
    """iOS glass card for one comic group's progress."""

    def __init__(self, comic_name: str, parent=None):
        super().__init__(parent)
        self._comic = comic_name
        self._collapsed = False
        self._cards: dict[str, _MiniBar] = {}

        self.setObjectName("glassProgressPanel")
        self.setStyleSheet("""
            QFrame#glassProgressPanel {
                background: rgba(255,255,255,0.72);
                border: 0.5px solid rgba(0,0,0,0.06);
                border-radius: 16px;
                margin: 4px 0px;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        self._header = QFrame()
        self._header.setFixedHeight(50)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setStyleSheet("background: transparent; border: none; border-radius: 16px;")
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(16, 0, 10, 0)
        hl.setSpacing(10)

        title = QLabel(comic_name)
        title.setStyleSheet("font-size: 15px; font-weight: 590; color: #1c1c1e; background: transparent; border: none;")
        hl.addWidget(title)

        hl.addStretch()

        self._info = QLabel("")
        self._info.setStyleSheet("font-size: 12px; font-weight: 480; color: #8e8e93; background: transparent; border: none;")
        hl.addWidget(self._info)

        self._group_bar = QProgressBar()
        self._group_bar.setRange(0, 100)
        self._group_bar.setFixedSize(120, 6)
        self._group_bar.setTextVisible(False)
        self._group_bar.setStyleSheet("""
            QProgressBar {
                border: none; border-radius: 3px; background: rgba(0,0,0,0.06);
            }
            QProgressBar::chunk { border-radius: 3px; background: #007aff; }
        """)
        hl.addWidget(self._group_bar)

        self._chevron = QPushButton()
        self._chevron.setFlat(True)
        self._chevron.setFixedSize(28, 28)
        self._chevron.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chevron.clicked.connect(self._toggle)
        self._set_chevron_collapsed()
        hl.addWidget(self._chevron)

        self._header.mousePressEvent = lambda e: self._toggle()
        outer.addWidget(self._header)

        # Body
        self._body = QFrame()
        self._body.setStyleSheet("background: transparent; border: none; border-radius: 0px 0px 16px 16px;")
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(16, 0, 16, 12)
        self._body_lay.setSpacing(4)
        outer.addWidget(self._body)

    def _set_chevron_collapsed(self):
        self._chevron.setText("›")
        self._chevron.setStyleSheet("""
            QPushButton {
                font-size: 20px; font-weight: 200; color: #aeaeb2;
                border: none; background: transparent; padding: 0px;
            }
            QPushButton:hover { color: #3c3c43; }
        """)

    def _set_chevron_expanded(self):
        self._chevron.setText("⌄")
        self._chevron.setStyleSheet("""
            QPushButton {
                font-size: 16px; font-weight: 400; color: #007aff;
                border: none; background: transparent; padding: 0px;
            }
            QPushButton:hover { color: #0055cc; }
        """)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)
        if self._collapsed:
            self._set_chevron_collapsed()
        else:
            self._set_chevron_expanded()

    def add_card(self, tid: str, name: str):
        card = _MiniBar(tid, name)
        self._body_lay.addWidget(card)
        self._cards[tid] = card

    def update_card(self, task: TaskItem):
        c = self._cards.get(task.task_id)
        if c:
            c.update_from_task(task)
        self._recalc()

    def _recalc(self):
        if not self._cards:
            return
        vals = [c._bar.value() for c in self._cards.values()]
        avg = sum(vals) // len(vals)
        self._group_bar.setValue(avg)

        done = sum(1 for c in self._cards.values() if c._status == "done")
        err = sum(1 for c in self._cards.values() if c._status == "error")
        run = len(self._cards) - done - err

        if done == len(self._cards):
            self._group_bar.setStyleSheet("QProgressBar { border: none; border-radius: 3px; background: rgba(52,199,89,0.12); } QProgressBar::chunk { border-radius: 3px; background: #34c759; }")
            self._info.setText(f"{len(self._cards)} 文件 · 全部完成")
        elif err and run == 0:
            self._group_bar.setStyleSheet("QProgressBar { border: none; border-radius: 3px; background: rgba(255,59,48,0.12); } QProgressBar::chunk { border-radius: 3px; background: #ff3b30; }")
            self._info.setText(f"{len(self._cards)} 文件 · {err} 失败")
        else:
            self._group_bar.setStyleSheet("QProgressBar { border: none; border-radius: 3px; background: rgba(0,0,0,0.06); } QProgressBar::chunk { border-radius: 3px; background: #007aff; }")
            self._info.setText(f"{len(self._cards)} 文件 · {run} 处理中")

    def cards(self):
        return self._cards

    def has_task(self, tid):
        return tid in self._cards


class _MiniBar(QFrame):
    """Single file progress row."""

    def __init__(self, tid: str, name: str, parent=None):
        super().__init__(parent)
        self.task_id = tid
        self._status = "pending"
        self.setStyleSheet("background: transparent; border: none;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(4)

        top = QHBoxLayout()
        nl = QLabel(name)
        nl.setStyleSheet("font-size: 12px; font-weight: 480; color: #3c3c43; background: transparent;")
        top.addWidget(nl)
        top.addStretch()
        self._sl = QLabel("等待中")
        self._sl.setStyleSheet("font-size: 11px; color: #8e8e93; background: transparent;")
        top.addWidget(self._sl)
        lay.addLayout(top)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setFixedHeight(4)
        self._bar.setTextVisible(False)
        self._bar.setStyleSheet("QProgressBar { border: none; border-radius: 2px; background: rgba(0,0,0,0.06); } QProgressBar::chunk { border-radius: 2px; background: #007aff; }")
        lay.addWidget(self._bar)

    def update_from_task(self, task: TaskItem):
        self._bar.setValue(task.progress)
        lb = {"pending": "等待中", "running": "处理中", "done": "已完成", "error": "失败"}
        self._status = task.status.value
        self._sl.setText(lb.get(self._status, self._status))

        if self._status == "done":
            self._sl.setStyleSheet("font-size: 11px; color: #34c759; font-weight: 540; background: transparent;")
            self._bar.setStyleSheet("QProgressBar { border: none; border-radius: 2px; background: rgba(52,199,89,0.12); } QProgressBar::chunk { border-radius: 2px; background: #34c759; }")
        elif self._status == "error":
            self._sl.setStyleSheet("font-size: 11px; color: #ff3b30; font-weight: 540; background: transparent;")
            self._bar.setStyleSheet("QProgressBar { border: none; border-radius: 2px; background: rgba(255,59,48,0.12); } QProgressBar::chunk { border-radius: 2px; background: #ff3b30; }")
        elif self._status == "running":
            self._sl.setStyleSheet("font-size: 11px; color: #007aff; font-weight: 540; background: transparent;")
            self._bar.setStyleSheet("QProgressBar { border: none; border-radius: 2px; background: rgba(0,0,0,0.06); } QProgressBar::chunk { border-radius: 2px; background: #007aff; }")


class ProgressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

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

        # Panels
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._container_lay = QVBoxLayout(self._container)
        self._container_lay.setContentsMargins(0, 0, 0, 0)
        self._container_lay.setSpacing(6)
        self._container_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._container_lay.addStretch()
        scroll.setWidget(self._container)
        layout.addWidget(scroll, stretch=1)

        self._panels: dict[str, _GlassProgressPanel] = {}
        self._tid_to_comic: dict[str, str] = {}

    def register_task(self, tid: str, name: str):
        comic = extract_comic_name(name)
        self._tid_to_comic[tid] = comic
        if comic not in self._panels:
            p = _GlassProgressPanel(comic)
            self._container_lay.insertWidget(self._container_lay.count() - 1, p)
            self._panels[comic] = p
        self._panels[comic].add_card(tid, name)

    def update_task(self, task: TaskItem):
        comic = self._tid_to_comic.get(task.task_id)
        if comic and comic in self._panels:
            self._panels[comic].update_card(task)
        self._recalc()

    def _recalc(self):
        if not self._panels:
            self._overall_bar.setValue(0)
            self._overall_lbl.setText("就绪")
            return
        vals = []
        done = err = 0
        for p in self._panels.values():
            for c in p.cards().values():
                vals.append(c._bar.value())
                if c._status == "done": done += 1
                elif c._status == "error": err += 1
        if not vals:
            return
        self._overall_bar.setValue(sum(vals) // len(vals))
        run = len(vals) - done - err
        parts = []
        if run: parts.append(f"{run} 处理中")
        if done: parts.append(f"{done} 完成")
        if err: parts.append(f"{err} 失败")
        self._overall_lbl.setText(", ".join(parts) if parts else "空闲")

    def clear(self):
        for p in self._panels.values():
            self._container_lay.removeWidget(p)
            p.deleteLater()
        self._panels.clear()
        self._tid_to_comic.clear()
        self._overall_bar.setValue(0)
        self._overall_lbl.setText("就绪")
