from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from typing import Callable

import img2pdf
from natsort import natsorted

from src.utils.helpers import is_image_file


def convert_archive_to_pdf(
    archive_path: str,
    output_dir: str,
    progress_cb: Callable[[int, str], None],
    delete_source: bool = False,
) -> str:
    archive_name = os.path.splitext(os.path.basename(archive_path))[0]
    output_path = os.path.join(output_dir, f"{archive_name}.pdf")

    temp_dir = tempfile.mkdtemp(prefix="comic_binder_")

    try:
        progress_cb(5, "正在解压压缩包...")
        _extract_archive(archive_path, temp_dir)

        progress_cb(30, "正在查找图片...")
        image_paths = _collect_images(temp_dir)
        if not image_paths:
            raise ValueError("压缩包中未找到图片文件")

        image_paths = natsorted(image_paths)

        progress_cb(50, f"正在将{len(image_paths)}张图片转换为PDF...")
        _images_to_pdf(image_paths, output_path, progress_cb)

        if delete_source:
            progress_cb(95, "正在删除源压缩包...")
            try:
                os.remove(archive_path)
            except OSError:
                pass

        progress_cb(100, "完成")
        return output_path

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _extract_archive(archive_path: str, dest_dir: str):
    ext = os.path.splitext(archive_path)[1].lower()

    if ext in (".zip", ".cbz"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(dest_dir)
    elif ext in (".rar", ".cbr"):
        import rarfile
        with rarfile.RarFile(archive_path, "r") as rf:
            rf.extractall(dest_dir)
    elif ext == ".7z":
        import py7zr
        with py7zr.SevenZipFile(archive_path, "r") as szf:
            szf.extractall(dest_dir)
    else:
        import patoolib
        patoolib.extract_archive(archive_path, outdir=dest_dir, interactive=False)


def _collect_images(base_dir: str) -> list[str]:
    images: list[str] = []
    for root, _dirs, files in os.walk(base_dir):
        for fname in files:
            if is_image_file(fname):
                images.append(os.path.join(root, fname))
    return images


def _images_to_pdf(
    image_paths: list[str],
    output_path: str,
    progress_cb: Callable[[int, str], None],
):
    total = len(image_paths)

    def _reader():
        for idx, img_path in enumerate(image_paths):
            if idx % max(1, total // 20) == 0 or idx == total - 1:
                pct = 50 + int((idx + 1) / total * 45)
                progress_cb(pct, f"正在处理第{idx + 1}/{total}张图片...")
            with open(img_path, "rb") as f:
                yield f.read()

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as out:
        out.write(img2pdf.convert(list(_reader())))
