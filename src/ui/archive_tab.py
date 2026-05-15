from __future__ import annotations

import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QFileDialog, QCheckBox, QMessageBox, QLabel,
    QStackedWidget, QFrame,
)

from src.core.archive_scanner import scan_archives, ArchiveFile
from src.core.archive_converter import convert_archive_to_pdf
from src.core.task_manager import TaskManager, TaskStatus
from src.ui.widgets.file_list_widget import FileListWidget
from src.ui.widgets.progress_widget import ProgressWidget
from src.utils.settings import get_last_path, set_last_path
from src.utils.comic_grouper import organize_comics_into_folders


class ArchiveTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._task_manager = TaskManager()
        self._archive_files: list[ArchiveFile] = []

        layout = QVBoxLayout(self)

        # Step indicator
        self._step_stack = QStackedWidget()
        layout.addWidget(self._step_stack)

        # --- Step 1: Folder Setup ---
        self._step1 = QWidget()
        s1_layout = QVBoxLayout(self._step1)
        s1_layout.setContentsMargins(8, 8, 8, 8)
        s1_layout.setSpacing(12)

        # Input card
        in_card = QFrame()
        in_card.setObjectName("glassCard")
        in_lay = QVBoxLayout(in_card)
        in_lay.setContentsMargins(16, 14, 16, 14)
        in_lay.setSpacing(8)
        in_label = QLabel("输入文件夹")
        in_label.setStyleSheet("font-size: 12px; font-weight: 590; color: #8e8e93; background: transparent; border: none;")
        in_lay.addWidget(in_label)
        in_row = QHBoxLayout()
        in_row.setSpacing(8)
        self._input_dir_edit = QLineEdit()
        self._input_dir_edit.setPlaceholderText("选择包含压缩包的文件夹...")
        restored_input = get_last_path("archive/input_dir")
        if restored_input:
            self._input_dir_edit.setText(restored_input)
        in_row.addWidget(self._input_dir_edit, stretch=1)
        in_browse = QPushButton("浏览")
        in_browse.clicked.connect(self._browse_input)
        in_row.addWidget(in_browse)
        in_lay.addLayout(in_row)
        s1_layout.addWidget(in_card)

        # Output card
        out_card = QFrame()
        out_card.setObjectName("glassCard")
        out_lay = QVBoxLayout(out_card)
        out_lay.setContentsMargins(16, 14, 16, 14)
        out_lay.setSpacing(8)
        out_label = QLabel("输出文件夹")
        out_label.setStyleSheet("font-size: 12px; font-weight: 590; color: #8e8e93; background: transparent; border: none;")
        out_lay.addWidget(out_label)
        out_row = QHBoxLayout()
        out_row.setSpacing(8)
        self._output_dir_edit = QLineEdit()
        self._output_dir_edit.setPlaceholderText("选择PDF输出文件夹...")
        restored_output = get_last_path("archive/output_dir")
        if restored_output:
            self._output_dir_edit.setText(restored_output)
        out_row.addWidget(self._output_dir_edit, stretch=1)
        out_browse = QPushButton("浏览")
        out_browse.clicked.connect(self._browse_output)
        out_row.addWidget(out_browse)
        out_lay.addLayout(out_row)
        s1_layout.addWidget(out_card)

        s1_layout.addSpacing(8)
        scan_layout = QHBoxLayout()
        scan_layout.addStretch()
        self._scan_btn = QPushButton("扫描压缩包")
        self._scan_btn.setObjectName("primaryBtn")
        self._scan_btn.setMinimumHeight(44)
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
            columns=["文件名", "大小", "类型", "状态"]
        )

        s2_layout.addWidget(self._file_list)

        bottom_row = QHBoxLayout()
        self._delete_source_cb = QCheckBox("转换完成后删除源压缩包")
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

        # Show step 1 by default
        self._step_stack.setCurrentIndex(0)

        # Connect task manager signals
        self._task_manager.signals.progress_updated.connect(self._on_progress)
        self._task_manager.signals.task_finished.connect(self._on_task_finished)
        self._task_manager.signals.all_finished.connect(self._on_all_finished)

    def _browse_input(self):
        path = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if path:
            self._input_dir_edit.setText(path)
            set_last_path("archive/input_dir", path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if path:
            self._output_dir_edit.setText(path)
            set_last_path("archive/output_dir", path)

    def _scan(self):
        input_dir = self._input_dir_edit.text().strip()
        output_dir = self._output_dir_edit.text().strip()

        if not input_dir:
            QMessageBox.warning(self, "警告", "请选择输入文件夹。")
            return
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出文件夹。")
            return

        set_last_path("archive/input_dir", input_dir)
        set_last_path("archive/output_dir", output_dir)

        self._archive_files = scan_archives(input_dir)

        if not self._archive_files:
            QMessageBox.information(self, "未找到压缩包", "所选文件夹中未找到压缩包文件。")
            return

        data = []
        for af in self._archive_files:
            data.append({
                "文件名": af.name,
                "大小": af.size_display,
                "类型": af.archive_type,
                "状态": "就绪",
                "selected": af.selected,
                "_archive": af,
            })

        self._file_list.set_data(data)
        self._step_stack.setCurrentIndex(1)

    def _go_to_step1(self):
        self._step_stack.setCurrentIndex(0)

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

            delete_source = self._delete_source_cb.isChecked()
            self._pending_output_dir = output_dir

            self._task_manager.clear_tasks()
            self._progress_widget.clear()

            for item in selected:
                archive: ArchiveFile = item["_archive"]
                self._task_manager.add_task(
                    task_id=archive.path,
                    name=archive.name,
                    metadata={
                        "archive_path": archive.path,
                        "output_dir": output_dir,
                        "delete_source": delete_source,
                    },
                )
                self._progress_widget.register_task(archive.path, archive.name)

            self._start_btn.setEnabled(False)
            self._cancel_btn.setVisible(True)
            self._done_btn.setVisible(False)
            self._open_folder_btn.setVisible(False)
            self._step_stack.setCurrentIndex(2)

            self._task_manager.run(self._worker_fn)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动转换失败：{e}")

    def _worker_fn(self, task, progress_cb):
        convert_archive_to_pdf(
            archive_path=task.metadata["archive_path"],
            output_dir=task.metadata["output_dir"],
            progress_cb=progress_cb,
            delete_source=task.metadata["delete_source"],
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
        if output_dir and os.path.isdir(output_dir):
            organize_comics_into_folders(output_dir, {".pdf"})

    def _cancel(self):
        self._task_manager.cancel_all()
        self._cancel_btn.setVisible(False)
        self._done_btn.setVisible(True)

    def _open_output_folder(self):
        output_dir = getattr(self, "_pending_output_dir", "")
        if output_dir and os.path.isdir(output_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))
        self._cancel_btn.setVisible(False)
        self._done_btn.setVisible(True)
