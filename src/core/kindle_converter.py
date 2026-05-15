from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import Callable


def convert_kindle_file(
    azw_path: str,
    output_dir: str,
    output_format: str,
    progress_cb: Callable[[int, str], None],
    delete_source: bool = False,
    folder_path: str | None = None,
    ebook_convert_path: str = "ebook-convert",
    output_name: str | None = None,
) -> str:
    if output_name:
        safe_name = _sanitize_filename(output_name)
        base_name = safe_name
    else:
        base_name = os.path.splitext(os.path.basename(azw_path))[0]
    ext = output_format.lower()
    output_filename = f"{base_name}.{ext}"
    output_path = os.path.join(output_dir, output_filename)

    os.makedirs(output_dir, exist_ok=True)

    progress_cb(5, "开始转换...")

    cmd = [ebook_convert_path, azw_path, output_path]

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )

        last_pct = 5
        for line in process.stdout:
            pct = _parse_ebook_convert_progress(line)
            if pct is not None:
                mapped = 5 + int(pct * 0.85)
                if mapped > last_pct:
                    last_pct = mapped
                    progress_cb(mapped, f"转换中... {pct}%")

        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f"ebook-convert 异常退出\n文件：{azw_path}\n返回码：{process.returncode}")

        if not os.path.isfile(output_path):
            raise RuntimeError(f"输出文件未生成\n源文件：{azw_path}\n预期输出：{output_path}")

    except FileNotFoundError:
        raise RuntimeError(
            "未找到Calibre的ebook-convert，请安装Calibre。"
        )

    if delete_source and folder_path:
        progress_cb(90, "正在删除 Kindle 缓存源文件夹...")
        try:
            if os.path.isdir(folder_path):
                shutil.rmtree(folder_path, ignore_errors=True)
        except OSError:
            pass
    elif delete_source:
        progress_cb(90, "正在删除源文件...")
        try:
            os.remove(azw_path)
        except OSError:
            pass

    progress_cb(100, "完成")
    return output_path


_PCT_RE = re.compile(r"(\d{1,3})\s*%")


def _parse_ebook_convert_progress(line: str) -> int | None:
    m = _PCT_RE.search(line)
    if m:
        return int(m.group(1))
    return None


def _sanitize_filename(name: str) -> str:
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, "_")
    name = name.strip(". ")
    if not name:
        name = "untitled"
    return name
