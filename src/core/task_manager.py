from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from PySide6.QtCore import QObject, Signal, QThread


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


@dataclass
class TaskItem:
    task_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    status_text: str = ""
    error_message: str = ""
    metadata: dict = field(default_factory=dict)


class TaskSignals(QObject):
    progress_updated = Signal(str, int, str)
    task_finished = Signal(str, bool, str)
    all_finished = Signal()


class _WorkerThread(QThread):
    def __init__(self, task: TaskItem, worker_fn: Callable, signals: TaskSignals, parent=None):
        super().__init__(parent)
        self._task = task
        self._worker_fn = worker_fn
        self._signals = signals

    def run(self):
        task = self._task
        task.status = TaskStatus.RUNNING
        task.progress = 0
        task.status_text = "启动中..."
        self._signals.progress_updated.emit(task.task_id, 0, "启动中...")

        def progress_cb(percent: int, text: str):
            task.progress = percent
            task.status_text = text
            self._signals.progress_updated.emit(task.task_id, percent, text)

        try:
            self._worker_fn(task, progress_cb)
            task.status = TaskStatus.DONE
            task.progress = 100
            task.status_text = "完成"
            self._signals.task_finished.emit(task.task_id, True, "完成")
        except Exception as e:
            task.status = TaskStatus.ERROR
            task.error_message = str(e)
            task.status_text = str(e)
            self._signals.task_finished.emit(task.task_id, False, str(e))


class TaskManager(QObject):
    def __init__(self, max_workers: int | None = None, parent=None):
        super().__init__(parent)
        self._tasks: dict[str, TaskItem] = {}
        self._signals = TaskSignals()
        self._threads: list[_WorkerThread] = []
        self._cancel_requested = False
        if max_workers is None:
            max_workers = min(os.cpu_count() or 2, 4)
        self._max_workers = max_workers
        self._active_count = 0
        self._pending_tasks: list[TaskItem] = []
        self._worker_fn: Callable | None = None
        self._total_count = 0
        self._done_count = 0
        self._signals.task_finished.connect(self._on_task_done_slot)

    @property
    def signals(self) -> TaskSignals:
        return self._signals

    @property
    def tasks(self) -> dict[str, TaskItem]:
        return self._tasks

    def add_task(self, task_id: str, name: str, metadata: dict | None = None):
        self._tasks[task_id] = TaskItem(
            task_id=task_id,
            name=name,
            metadata=metadata or {},
        )

    def remove_task(self, task_id: str):
        self._tasks.pop(task_id, None)

    def clear_tasks(self):
        self._tasks.clear()

    def cancel_all(self):
        self._cancel_requested = True
        for t in self._threads:
            if t.isRunning():
                t.quit()
                t.wait(2000)
        self._threads.clear()
        self._pending_tasks.clear()
        self._active_count = 0

    def is_cancelled(self) -> bool:
        return self._cancel_requested

    def run(self, worker_fn: Callable):
        self._cancel_requested = False
        self._worker_fn = worker_fn
        pending = [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]

        if not pending:
            self._signals.all_finished.emit()
            return

        for t in self._threads:
            if t.isRunning():
                t.quit()
                t.wait(2000)
        self._threads.clear()

        self._pending_tasks = list(pending)
        self._active_count = 0
        self._total_count = len(pending)
        self._done_count = 0

        for _ in range(min(self._max_workers, len(self._pending_tasks))):
            self._start_next()

    def _on_task_done_slot(self, _task_id: str, _success: bool, _msg: str):
        if self._worker_fn is None:
            return
        self._done_count += 1
        self._active_count = max(0, self._active_count - 1)
        self._start_next()
        if self._done_count >= self._total_count:
            self._signals.all_finished.emit()
            self._worker_fn = None

    def _start_next(self):
        if self._cancel_requested:
            return
        if not self._pending_tasks:
            return
        if self._active_count >= self._max_workers:
            return

        task = self._pending_tasks.pop(0)
        self._active_count += 1
        thread = _WorkerThread(task, self._worker_fn, self._signals)
        self._threads.append(thread)
        thread.start()
