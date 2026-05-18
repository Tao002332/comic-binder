from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QEvent, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QCheckBox, QAbstractItemView,
    QMenu, QLabel, QFrame, QScrollArea, QSizePolicy,
)

from src.utils.comic_grouper import extract_comic_name
from src.ui.widgets.animated_checkbox import AnimatedCheckBox
from src.ui.widgets.custom_tooltip import install as install_tip, _get_tip

def _row_height(table: QTableWidget) -> int:
    fm = table.fontMetrics()
    return max(44, fm.height() + 24)

def _header_height(table: QTableWidget) -> int:
    return table.horizontalHeader().height()


class _GlassPanel(QFrame):
    """iOS-style glass card for one comic group."""

    def __init__(self, comic_name: str, collapsible: bool = True, parent=None):
        super().__init__(parent)
        self._comic = comic_name
        self._collapsed = False
        self._collapsible = collapsible
        self._file_indices: list[int] = []
        self._data_ref: list[dict] = []
        self._on_toggle_cb = None
        self._current_page = 0

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
        self._header.setCursor(Qt.CursorShape.PointingHandCursor if collapsible else Qt.CursorShape.ArrowCursor)
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
        title.setMaximumWidth(220)
        title.setWordWrap(False)
        install_tip(title, comic_name)
        hl.addWidget(title)

        hl.addStretch()

        self._info = QLabel("")
        self._info.setStyleSheet("font-size: 12px; font-weight: 480; color: #8e8e93; background: transparent; border: none;")
        hl.addWidget(self._info)

        if collapsible:
            self._chevron = QPushButton()
            self._chevron.setFlat(True)
            self._chevron.setFixedSize(28, 28)
            self._chevron.setCursor(Qt.CursorShape.PointingHandCursor)
            self._chevron.clicked.connect(self._toggle)
            self._set_chevron_collapsed()
            hl.addWidget(self._chevron)
            self._header.mousePressEvent = self._on_header_click
        else:
            self._chevron = None

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
        self._table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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
        self._table.setShowGrid(True)
        self._table.setMouseTracking(True)
        self._table.viewport().setCursor(Qt.CursorShape.ArrowCursor)
        self._table.setStyleSheet("""
            QTableWidget {
                border: none;
                background: transparent;
                alternate-background-color: rgba(0,0,0,0.02);
                gridline-color: rgba(0,0,0,0.04);
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

        # Cell tooltip on hover
        self._table.cellEntered.connect(self._on_cell_hover)
        self._table.viewport().installEventFilter(self)

        outer.addWidget(self._body)

    def _set_chevron_collapsed(self):
        if not self._chevron: return
        self._chevron.setText("›")
        self._chevron.setStyleSheet("""
            QPushButton { font-size: 20px; font-weight: 200; color: #aeaeb2; border: none; background: transparent; padding: 0px; }
            QPushButton:hover { color: #3c3c43; }
        """)

    def _set_chevron_expanded(self):
        if not self._chevron: return
        self._chevron.setText("⌄")
        self._chevron.setStyleSheet("""
            QPushButton { font-size: 16px; font-weight: 400; color: #007aff; border: none; background: transparent; padding: 0px; }
            QPushButton:hover { color: #0055cc; }
        """)

    def _on_header_click(self, _event):
        if self._collapsible:
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
        self._columns = columns
        self._current_page = 0

        self._table.setColumnCount(len(columns) + 1)
        labels = [""] + list(columns)
        self._table.setHorizontalHeaderLabels(labels)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 40)
        for i in range(len(columns)):
            header.setSectionResizeMode(i + 1, QHeaderView.ResizeMode.Stretch)


        # Auto-height for <=10 rows, fixed 10-row + scrollbar for >10
        total = len(indices)
        rh = _row_height(self._table)
        hh = _header_height(self._table)
        self._table.setMinimumHeight(hh)
        if total <= 10:
            self._table.setMaximumHeight(16777215)
            self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            self._table.setMaximumHeight(10 * rh + hh)
            self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._render_all_rows(indices)

        all_sel = True
        sel_count = 0
        for idx in indices:
            item = data[idx]
            if item.get("selected", True):
                sel_count += 1
            else:
                all_sel = False

        self._group_cb.blockSignals(True)
        self._group_cb.setChecked(all_sel)
        self._group_cb.blockSignals(False)
        self._group_cb.toggled.connect(self._on_group_toggle)

        self._info.setText(f"{len(indices)} 个文件 · {sel_count} 已选")

    def _render_all_rows(self, indices: list[int]):
        self._table.setRowCount(0)
        for idx in indices:
            item = self._data_ref[idx]
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setRowHeight(row, _row_height(self._table))

            cb = AnimatedCheckBox()
            cb.setChecked(item.get("selected", True))
            cb.toggled.connect(lambda checked, r=idx: self._on_file_toggle(r, checked))
            wrapper = QWidget()
            wrapper.setStyleSheet("background: transparent;")
            wl = QHBoxLayout(wrapper)
            wl.addWidget(cb)
            wl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            wl.setContentsMargins(0, 0, 0, 0)
            self._table.setCellWidget(row, 0, wrapper)

            for ci, col_name in enumerate(self._columns):
                val = item.get(col_name, "")
                t = QTableWidgetItem(str(val))
                t.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                self._table.setItem(row, ci + 1, t)

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
        self._render_all_rows(self._file_indices)
        sel = len(self._file_indices) if checked else 0
        self._info.setText(f"{len(self._file_indices)} 个文件 · {sel} 已选")
        if self._on_toggle_cb:
            self._on_toggle_cb()

    def _on_cell_hover(self, row: int, col: int):
        if row < 0 or col < 1:
            _get_tip().hide()
            return
        item = self._table.item(row, col)
        if item:
            text = item.text()
            fm = self._table.fontMetrics()
            col_w = self._table.columnWidth(col)
            if fm.horizontalAdvance(text) > col_w - 16:
                rect = self._table.visualItemRect(item)
                pos = self._table.viewport().mapToGlobal(rect.topLeft())
                pos.setY(pos.y() - _get_tip().height() - 4)
                _get_tip().show_text(text, None)
                _get_tip().move(pos)

    def eventFilter(self, obj, event):
        if obj is self._table.viewport():
            if event.type() == QEvent.Type.Leave:
                _get_tip().hide()
        return super().eventFilter(obj, event)

    @property
    def file_indices(self):
        return self._file_indices

    @property
    def group_cb(self):
        return self._group_cb

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

    def __init__(self, columns: list[str], grouped: bool = True, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._grouped = grouped
        self._data: list[dict] = []
        self._groups: dict[str, list[int]] = {}
        self._panels: dict[str, _GlassPanel] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Top bar
        top = QHBoxLayout()
        top.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索...")
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self._do_search)
        self._search.textChanged.connect(lambda: self._search_timer.start())
        top.addWidget(self._search)

        if grouped:
            for text, slot in [("展开全部", self._expand_all), ("折叠全部", self._collapse_all)]:
                btn = QPushButton(text)
                btn.clicked.connect(slot)
                top.addWidget(btn)

        for text, slot in [("全选", self._select_all), ("取消全选", self._deselect_all)]:
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

        # Panels container (no outer scroll area, panel auto-fits table)
        self._container_lay = QVBoxLayout()
        self._container_lay.setContentsMargins(0, 0, 0, 0)
        self._container_lay.setSpacing(6)
        self._container_lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addLayout(self._container_lay, stretch=1)

    @property
    def search_input(self):
        return self._search

    def set_data(self, data: list[dict]):
        self.setUpdatesEnabled(False)
        # Sort by comic name
        self._data = sorted(data, key=lambda it: self._comic_name(it).lower())
        self._rebuild_groups()
        self._rebuild_panels()
        self.setUpdatesEnabled(True)

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
        if not self._grouped:
            # Flat mode: all files in one group
            all_indices = list(range(len(self._data)))
            if all_indices:
                self._groups[""] = all_indices
        else:
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

            collapsible = self._grouped and comic != ""
            title = comic if comic else "全部文件"
            panel = _GlassPanel(title, collapsible=collapsible)
            panel.set_files(visible, self._data, self._columns)
            panel.set_toggle_callback(lambda: self.selection_changed.emit())
            self._container_lay.insertWidget(self._container_lay.count(), panel)
            self._panels[comic] = panel

        self._update_count()

    def _do_search(self):
        self.setUpdatesEnabled(False)
        self._rebuild_panels()
        self.setUpdatesEnabled(True)

    def _expand_all(self):
        for p in self._panels.values():
            if p._collapsed: p._toggle()

    def _collapse_all(self):
        for p in self._panels.values():
            if not p._collapsed: p._toggle()

    def _select_all(self):
        self.setUpdatesEnabled(False)
        for it in self._data: it["selected"] = True
        self._rebuild_panels()
        self.setUpdatesEnabled(True)
        self.selection_changed.emit()

    def _deselect_all(self):
        self.setUpdatesEnabled(False)
        for it in self._data: it["selected"] = False
        self._rebuild_panels()
        self.setUpdatesEnabled(True)
        self.selection_changed.emit()

    def _remove_selected(self):
        to_rm = [it for it in self._data if it.get("selected", True)]
        remaining = [it for it in self._data if not it.get("selected", True)]
        if to_rm:
            self.setUpdatesEnabled(False)
            self._data = remaining
            self._rebuild_groups()
            self._rebuild_panels()
            self.setUpdatesEnabled(True)
            self.remove_requested.emit(to_rm)

    def _update_count(self):
        if not self._data:
            self._count_lbl.setText("")
            return
        sel = sum(1 for it in self._data if it.get("selected", True))
        self._count_lbl.setText(f"{len(self._groups)} 部 · {len(self._data)} 文件 · {sel} 已选")
