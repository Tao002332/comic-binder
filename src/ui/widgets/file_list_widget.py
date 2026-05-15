from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QCheckBox, QAbstractItemView,
    QMenu, QLabel, QFrame, QScrollArea,
)

from src.utils.comic_grouper import extract_comic_name
from src.ui.widgets.animated_checkbox import AnimatedCheckBox

class _GlassPanel(QFrame):
    """iOS-style glass card for one comic group."""

    def __init__(self, comic_name: str, parent=None):
        super().__init__(parent)
        self._comic = comic_name
        self._collapsed = False
        self._file_indices: list[int] = []
        self._data_ref: list[dict] = []
        self._on_toggle_cb = None

        self.setObjectName("glassCard")
        self.setStyleSheet("""
            QFrame#glassCard {
                background: rgba(255,255,255,0.72);
                border: 0.5px solid rgba(0,0,0,0.06);
                border-radius: 16px;
                margin: 4px 0px;
            }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # --- Header ---
        self._header = QFrame()
        self._header.setFixedHeight(50)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setStyleSheet("background: transparent; border: none;")
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(16, 0, 14, 0)
        hl.setSpacing(10)
        hl.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._group_cb = AnimatedCheckBox()
        self._group_cb.setChecked(True)
        hl.addWidget(self._group_cb)

        title = QLabel(comic_name)
        title.setStyleSheet("font-size: 15px; font-weight: 590; color: #1c1c1e; background: transparent; border: none;")
        hl.addWidget(title)

        hl.addStretch()

        self._info = QLabel("")
        self._info.setStyleSheet("font-size: 12px; font-weight: 480; color: #8e8e93; background: transparent; border: none;")
        hl.addWidget(self._info)

        self._chevron = QPushButton()
        self._chevron.setFlat(True)
        self._chevron.setFixedSize(28, 28)
        self._chevron.setCursor(Qt.CursorShape.PointingHandCursor)
        self._chevron.clicked.connect(self._toggle)
        self._set_chevron_collapsed()
        hl.addWidget(self._chevron)

        self._header.mousePressEvent = self._on_header_click
        outer.addWidget(self._header)

        # --- Body ---
        self._body = QFrame()
        self._body.setStyleSheet("background: transparent; border: none; border-radius: 0px 0px 16px 16px;")
        body_lay = QVBoxLayout(self._body)
        body_lay.setContentsMargins(12, 0, 12, 12)
        body_lay.setSpacing(0)

        self._table = QTableWidget()
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setVisible(True)
        self._table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._table.horizontalHeader().setFixedHeight(32)
        self._table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background: rgba(0,0,0,0.03);
                color: #8e8e93;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid rgba(0,0,0,0.06);
                font-size: 11px;
                font-weight: 600;
            }
        """)
        self._table.setShowGrid(False)
        self._table.setMouseTracking(True)
        self._table.setStyleSheet("""
            QTableWidget {
                border: none;
                background: transparent;
                alternate-background-color: rgba(0,0,0,0.02);
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 0.5px solid rgba(0,0,0,0.04);
                font-size: 13px;
                color: #3c3c43;
                background: transparent;
            }
            QTableWidget::item:selected {
                background-color: rgba(168, 85, 247, 0.06);
                color: #1c1c1e;
            }
        """)
        body_lay.addWidget(self._table)
        outer.addWidget(self._body)

    def _set_chevron_collapsed(self):
        self._chevron.setText("›")
        self._chevron.setStyleSheet("""
            QPushButton {
                font-size: 20px;
                font-weight: 200;
                color: #aeaeb2;
                border: none;
                background: transparent;
                padding: 0px;
            }
            QPushButton:hover { color: #3c3c43; }
        """)

    def _set_chevron_expanded(self):
        self._chevron.setText("⌄")
        self._chevron.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: 400;
                color: #007aff;
                border: none;
                background: transparent;
                padding: 0px;
            }
            QPushButton:hover { color: #0055cc; }
        """)

    def _on_header_click(self, _event):
        self._toggle()

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)
        if self._collapsed:
            self._set_chevron_collapsed()
        else:
            self._set_chevron_expanded()

    def set_files(self, indices: list[int], data: list[dict], columns: list[str]):
        self._file_indices = indices
        self._data_ref = data
        self._table.setColumnCount(len(columns) + 1)
        self._table.setRowCount(0)

        labels = [""] + list(columns)
        self._table.setHorizontalHeaderLabels(labels)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 42)
        for i in range(len(columns)):
            header.setSectionResizeMode(i + 1, QHeaderView.ResizeMode.Stretch)

        all_sel = True
        sel_count = 0
        for idx in indices:
            item = data[idx]
            if item.get("selected", True):
                sel_count += 1
            else:
                all_sel = False

            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setRowHeight(row, 42)

            cb = AnimatedCheckBox()
            cb.setChecked(item.get("selected", True))
            cb.toggled.connect(lambda checked, r=idx: self._on_file_toggle(r, checked))
            self._table.setCellWidget(row, 0, _center_widget(cb))

            for ci, col_name in enumerate(columns):
                val = item.get(col_name, "")
                t = QTableWidgetItem(str(val))
                t.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self._table.setItem(row, ci + 1, t)

        self._group_cb.blockSignals(True)
        self._group_cb.setChecked(all_sel)
        self._group_cb.blockSignals(False)
        self._group_cb.toggled.connect(self._on_group_toggle)

        self._info.setText(f"{len(indices)} 个文件 · {sel_count} 已选")

    def _on_file_toggle(self, idx: int, checked: bool):
        if 0 <= idx < len(self._data_ref):
            self._data_ref[idx]["selected"] = checked
        sel = sum(1 for i in self._file_indices if self._data_ref[i].get("selected", True))
        all_sel = sel == len(self._file_indices)
        self._group_cb.blockSignals(True)
        self._group_cb.setChecked(all_sel)
        self._group_cb.blockSignals(False)
        self._info.setText(f"{len(self._file_indices)} 个文件 · {sel} 已选")
        if self._on_toggle_cb:
            self._on_toggle_cb()

    def _on_group_toggle(self, checked: bool):
        for idx in self._file_indices:
            self._data_ref[idx]["selected"] = checked
        for row in range(self._table.rowCount()):
            cb_w = self._table.cellWidget(row, 0)
            if cb_w:
                cb = cb_w.findChild(QCheckBox)
                if cb:
                    cb.blockSignals(True)
                    cb.setChecked(checked)
                    cb.blockSignals(False)
        sel = len(self._file_indices) if checked else 0
        self._info.setText(f"{len(self._file_indices)} 个文件 · {sel} 已选")
        if self._on_toggle_cb:
            self._on_toggle_cb()

    @property
    def file_indices(self):
        return self._file_indices

    @property
    def group_cb(self):
        return self._group_cb

    @property
    def table(self):
        return self._table

    def set_toggle_callback(self, cb):
        self._on_toggle_cb = cb


def _center_widget(widget: QWidget) -> QWidget:
    w = QWidget()
    w.setStyleSheet("background: transparent;")
    lay = QHBoxLayout(w)
    lay.addWidget(widget)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(0)
    return w


class FileListWidget(QWidget):
    selection_changed = Signal()
    remove_requested = Signal(list)

    def __init__(self, columns: list[str], parent=None):
        super().__init__(parent)
        self._columns = columns
        self._data: list[dict] = []
        self._groups: dict[str, list[int]] = {}
        self._panels: dict[str, _GlassPanel] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Top bar
        top = QHBoxLayout()
        top.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索...")
        self._search.textChanged.connect(self._on_search)
        top.addWidget(self._search)

        for text, slot in [("展开全部", self._expand_all), ("折叠全部", self._collapse_all),
                           ("全选", self._select_all), ("取消全选", self._deselect_all)]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            top.addWidget(btn)

        rm = QPushButton("删除选中")
        rm.clicked.connect(self._remove_selected)
        rm.setStyleSheet("QPushButton { color: #ff3b30; border-color: rgba(255,59,48,0.20); } QPushButton:hover { background: rgba(255,59,48,0.06); }")
        top.addWidget(rm)
        top.addStretch()

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet("font-size: 12px; color: #8e8e93; background: transparent;")
        top.addWidget(self._count_lbl)
        layout.addLayout(top)

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

    @property
    def search_input(self):
        return self._search

    def set_data(self, data: list[dict]):
        self._data = data
        self._rebuild_groups()
        self._rebuild_panels()

    def get_data(self):
        return list(self._data)

    def get_selected(self):
        return [it for it in self._data if it.get("selected", True)]

    def _comic_name(self, item):
        name = item.get("文件名") or item.get("解析标题") or item.get("原始ID") or ""
        noext = name.rsplit(".", 1)[0] if "." in name else name
        return extract_comic_name(noext)

    def _rebuild_groups(self):
        self._groups = {}
        for i, item in enumerate(self._data):
            c = self._comic_name(item)
            self._groups.setdefault(c, []).append(i)

    def _rebuild_panels(self):
        for p in self._panels.values():
            self._container_lay.removeWidget(p)
            p.deleteLater()
        self._panels.clear()

        ft = self._search.text().strip().lower()
        for comic, indices in self._groups.items():
            visible = [i for i in indices if not ft or
                       ft in comic.lower() or
                       ft in " ".join(str(v) for k, v in self._data[i].items()
                                       if k not in ("selected", "_archive", "_kindle")).lower()]
            if not visible:
                continue

            panel = _GlassPanel(comic)
            panel.set_files(visible, self._data, self._columns)
            panel.set_toggle_callback(lambda: self.selection_changed.emit())
            self._container_lay.insertWidget(self._container_lay.count() - 1, panel)
            self._panels[comic] = panel

        self._update_count()

    def _on_search(self):
        self._rebuild_panels()

    def _expand_all(self):
        for p in self._panels.values():
            if p._collapsed: p._toggle()

    def _collapse_all(self):
        for p in self._panels.values():
            if not p._collapsed: p._toggle()

    def _select_all(self):
        for it in self._data: it["selected"] = True
        self._rebuild_panels()
        self.selection_changed.emit()

    def _deselect_all(self):
        for it in self._data: it["selected"] = False
        self._rebuild_panels()
        self.selection_changed.emit()

    def _remove_selected(self):
        to_rm = [it for it in self._data if it.get("selected", True)]
        remaining = [it for it in self._data if not it.get("selected", True)]
        if to_rm:
            self._data = remaining
            self._rebuild_groups()
            self._rebuild_panels()
            self.remove_requested.emit(to_rm)

    def _update_count(self):
        if not self._data:
            self._count_lbl.setText("")
            return
        sel = sum(1 for it in self._data if it.get("selected", True))
        self._count_lbl.setText(f"{len(self._groups)} 部 · {len(self._data)} 文件 · {sel} 已选")
