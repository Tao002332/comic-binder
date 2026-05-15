from __future__ import annotations

import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QFileDialog, QCheckBox, QMessageBox, QLabel,
    QComboBox, QStackedWidget, QFrame,
)

from src.core.kindle_scanner import (
    scan_kindle_files, get_default_kindle_path, refresh_metadata, KindleFile,
)
from src.core.kindle_converter import convert_kindle_file
from src.core.task_manager import TaskManager, TaskStatus
from src.ui.widgets.file_list_widget import FileListWidget
from src.ui.widgets.progress_widget import ProgressWidget
from src.utils.helpers import KINDLE_OUTPUT_FORMATS
from src.utils.settings import (
    get_last_path, set_last_path,
    get_calibre_path, set_calibre_path,
    get_ebook_meta_path, get_ebook_convert_path,
)
from src.utils.comic_grouper import organize_comics_into_folders


class KindleTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_manager = TaskManager()
        self._kindle_files: list[KindleFile] = []

        layout = QVBoxLayout(self)

        self._step_stack = QStackedWidget()
        layout.addWidget(self._step_stack)

        # --- Step 1: Source Setup ---
        self._step1 = QWidget()
        s1_layout = QVBoxLayout(self._step1)
        s1_layout.setContentsMargins(8, 8, 8, 8)
        s1_layout.setSpacing(12)

        def _make_card(title, placeholder, saved_key, browse_slot, default_path=None):
            card = QFrame()
            card.setObjectName("glassCard")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 14, 16, 14)
            cl.setSpacing(8)
            tl = QLabel(title)
            tl.setStyleSheet("font-size: 12px; font-weight: 590; color: #8e8e93; background: transparent; border: none;")
            cl.addWidget(tl)
            row = QHBoxLayout()
            row.setSpacing(8)
            edit = QLineEdit()
            edit.setPlaceholderText(placeholder)
            restored = get_last_path(saved_key)
            if restored:
                edit.setText(restored)
            elif default_path and os.path.isdir(default_path):
                edit.setText(default_path)
            row.addWidget(edit, stretch=1)
            btn = QPushButton("浏览")
            btn.clicked.connect(browse_slot)
            row.addWidget(btn)
            cl.addLayout(row)
            return card, edit

        in_card, self._input_dir_edit = _make_card(
            "Kindle缓存 / 输入文件夹",
            "My Kindle Content 文件夹路径...",
            "kindle/input_dir",
            self._browse_input,
            get_default_kindle_path()
        )
        s1_layout.addWidget(in_card)

        out_card, self._output_dir_edit = _make_card(
            "输出文件夹",
            "选择输出文件夹...",
            "kindle/output_dir",
            self._browse_output
        )
        s1_layout.addWidget(out_card)

        cal_card, self._calibre_dir_edit = _make_card(
            "Calibre 安装路径",
            "Calibre安装文件夹（留空则自动检测）...",
            "calibre/install_path",
            self._browse_calibre,
            get_calibre_path()
        )
        s1_layout.addWidget(cal_card)

        s1_layout.addSpacing(8)
        scan_layout = QHBoxLayout()
        scan_layout.addStretch()
        self._scan_btn = QPushButton("扫描Kindle文件")
        self._scan_btn.setMinimumHeight(44)
        self._scan_btn.setObjectName("primaryBtn")
        self._scan_btn.clicked.connect(self._scan)
        scan_layout.addWidget(self._scan_btn)
        scan_layout.addStretch()
        s1_layout.addLayout(scan_layout)
        s1_layout.addStretch()

        self._step_stack.addWidget(self._step1)

        # --- Step 2: File Management ---
        self._step2 = QWidget()
        s2_layout = QVBoxLayout(self._step2)
        s2_layout.setContentsMargins(0, 0, 0, 0)

        self._file_list = FileListWidget(
            columns=["原始ID", "解析标题", "大小", "状态"]
        )
        s2_layout.addWidget(self._file_list)

        mid_row = QHBoxLayout()
        self._format_label = QLabel("输出格式：")
        mid_row.addWidget(self._format_label)
        self._format_combo = QComboBox()
        self._format_combo.addItems(KINDLE_OUTPUT_FORMATS)
        self._format_combo.setCurrentText("PDF")
        mid_row.addWidget(self._format_combo)
        mid_row.addStretch()
        self._refresh_meta_btn = QPushButton("刷新元数据")
        self._refresh_meta_btn.clicked.connect(self._refresh_metadata)
        mid_row.addWidget(self._refresh_meta_btn)
        s2_layout.addLayout(mid_row)

        bottom_row = QHBoxLayout()
        self._delete_source_cb = QCheckBox("转换完成后删除源文件")
        bottom_row.addWidget(self._delete_source_cb)
        bottom_row.addStretch()

        self._back_btn = QPushButton("返回")
        self._back_btn.clicked.connect(self._go_to_step1)
        bottom_row.addWidget(self._back_btn)

        self._start_btn = QPushButton("开始转换")
        self._start_btn.setObjectName("primaryBtn")
        self._start_btn.setMinimumHeight(40)
        self._start_btn.clicked.connect(self._start_conversion)
        bottom_row.addWidget(self._start_btn)

        s2_layout.addLayout(bottom_row)
        self._step_stack.addWidget(self._step2)

        # --- Step 3: Progress ---
        self._step3 = QWidget()
        s3_layout = QVBoxLayout(self._step3)
        s3_layout.setContentsMargins(0, 0, 0, 0)

        self._progress_widget = ProgressWidget()
        s3_layout.addWidget(self._progress_widget)

        s3_bottom = QHBoxLayout()
        s3_bottom.addStretch()
        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.clicked.connect(self._cancel)
        s3_bottom.addWidget(self._cancel_btn)
        self._done_btn = QPushButton("返回首页")
        self._done_btn.clicked.connect(self._go_to_step1)
        self._done_btn.setVisible(False)
        s3_bottom.addWidget(self._done_btn)
        self._open_folder_btn = QPushButton("打开输出文件夹")
        self._open_folder_btn.clicked.connect(self._open_output_folder)
        self._open_folder_btn.setVisible(False)
        s3_bottom.addWidget(self._open_folder_btn)
        s3_layout.addLayout(s3_bottom)

        self._step_stack.addWidget(self._step3)

        self._step_stack.setCurrentIndex(0)

        self._task_manager.signals.progress_updated.connect(self._on_progress)
        self._task_manager.signals.task_finished.connect(self._on_task_finished)
        self._task_manager.signals.all_finished.connect(self._on_all_finished)

    def _browse_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择Kindle内容文件夹")
        if path:
            self._input_dir_edit.setText(path)
            set_last_path("kindle/input_dir", path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if path:
            self._output_dir_edit.setText(path)
            set_last_path("kindle/output_dir", path)

    def _browse_calibre(self):
        path = QFileDialog.getExistingDirectory(self, "选择Calibre安装文件夹")
        if path:
            self._calibre_dir_edit.setText(path)
            set_calibre_path(path)

    def _scan(self):
        input_dir = self._input_dir_edit.text().strip()
        output_dir = self._output_dir_edit.text().strip()
        calibre_dir = self._calibre_dir_edit.text().strip()

        if not input_dir:
            QMessageBox.warning(self, "警告", "请选择输入文件夹。")
            return
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出文件夹。")
            return

        set_last_path("kindle/input_dir", input_dir)
        set_last_path("kindle/output_dir", output_dir)
        if calibre_dir:
            set_calibre_path(calibre_dir)

        ebook_meta_path = get_ebook_meta_path()
        self._kindle_files = scan_kindle_files(input_dir, ebook_meta_path=ebook_meta_path)

        if not self._kindle_files:
            QMessageBox.information(
                self, "未找到文件",
                "未找到Kindle PDOC文件。\n\n"
                "期望的目录结构：\n"
                "  My Kindle Content/\n"
                "    {ID}_PDOC/\n"
                "      {ID}_PDOC.azw"
            )
            return

        self._show_step2()

    def _show_step2(self):
        data = []
        for kf in self._kindle_files:
            data.append({
                "原始ID": kf.original_id,
                "解析标题": kf.parsed_title or "（未知）",
                "大小": kf.size_display,
                "状态": "就绪",
                "selected": kf.selected,
                "_kindle": kf,
            })

        self._file_list.set_data(data)
        self._step_stack.setCurrentIndex(1)

    def _go_to_step1(self):
        self._step_stack.setCurrentIndex(0)

    def _refresh_metadata(self):
        ebook_meta_path = get_ebook_meta_path()
        data = self._file_list.get_data()
        for item in data:
            kf: KindleFile = item["_kindle"]
            refresh_metadata(kf, ebook_meta_path=ebook_meta_path)
            item["解析标题"] = kf.parsed_title or "（未知）"
        self._file_list.set_data(data)
        QMessageBox.information(self, "完成", "元数据已刷新。")

    def _start_conversion(self):
        try:
            selected = self._file_list.get_selected()
            if not selected:
                QMessageBox.warning(self, "警告", "未选择要转换的文件。")
                return

            output_dir = self._output_dir_edit.text().strip()
            if not output_dir or not os.path.isdir(output_dir):
                QMessageBox.warning(self, "警告", "输出文件夹不存在，请重新选择。")
                return

            output_format = self._format_combo.currentText()
            delete_source = self._delete_source_cb.isChecked()
            self._pending_output_dir = output_dir
            self._pending_output_format = output_format

            self._task_manager.clear_tasks()
            self._progress_widget.clear()

            for item in selected:
                kf: KindleFile = item["_kindle"]
                task_id = kf.azw_path
                self._task_manager.add_task(
                    task_id=task_id,
                    name=kf.display_name,
                    metadata={
                        "azw_path": kf.azw_path,
                        "output_dir": output_dir,
                        "output_format": output_format,
                        "delete_source": delete_source,
                        "folder_path": kf.folder_path,
                        "output_name": kf.parsed_title or None,
                    },
                )
                self._progress_widget.register_task(task_id, kf.display_name)

            self._start_btn.setEnabled(False)
            self._cancel_btn.setVisible(True)
            self._done_btn.setVisible(False)
            self._open_folder_btn.setVisible(False)
            self._step_stack.setCurrentIndex(2)

            self._task_manager.run(self._worker_fn)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动转换失败：{e}")

    def _worker_fn(self, task, progress_cb):
        convert_kindle_file(
            azw_path=task.metadata["azw_path"],
            output_dir=task.metadata["output_dir"],
            output_format=task.metadata["output_format"],
            progress_cb=progress_cb,
            delete_source=task.metadata["delete_source"],
            folder_path=task.metadata["folder_path"],
            ebook_convert_path=get_ebook_convert_path(),
            output_name=task.metadata.get("output_name"),
        )

    def _on_progress(self, task_id: str, percent: int, text: str):
        task = self._task_manager.tasks.get(task_id)
        if task:
            task.progress = percent
            task.status_text = text
            self._progress_widget.update_task(task)

    def _on_task_finished(self, task_id: str, success: bool, message: str):
        task = self._task_manager.tasks.get(task_id)
        if task:
            task.status = TaskStatus.DONE if success else TaskStatus.ERROR
            task.status_text = message
            if not success:
                task.error_message = message
            self._progress_widget.update_task(task)

    def _on_all_finished(self):
        self._cancel_btn.setVisible(False)
        self._done_btn.setVisible(True)
        self._open_folder_btn.setVisible(True)
        self._start_btn.setEnabled(True)

        output_dir = getattr(self, "_pending_output_dir", "")
        output_format = getattr(self, "_pending_output_format", "PDF")
        ext = f".{output_format.lower()}"
        if output_dir and os.path.isdir(output_dir):
            organize_comics_into_folders(output_dir, {ext})

    def _cancel(self):
        self._task_manager.cancel_all()
        self._cancel_btn.setVisible(False)
        self._done_btn.setVisible(True)

    def _open_output_folder(self):
        output_dir = getattr(self, "_pending_output_dir", "")
        if output_dir and os.path.isdir(output_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))
