from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field

from src.utils.helpers import format_size


@dataclass
class KindleFile:
    folder_path: str
    azw_path: str
    original_id: str
    parsed_title: str
    size: int
    selected: bool = True

    @property
    def display_name(self) -> str:
        return self.parsed_title or self.original_id

    @property
    def size_display(self) -> str:
        return format_size(self.size)


_PDOC_PATTERN = re.compile(r"^([A-Z0-9]+_PDOC)$", re.IGNORECASE)


def get_default_kindle_path() -> str:
    import platform
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Windows":
        return os.path.join(home, "Documents", "My Kindle Content")
    elif system == "Darwin":
        return os.path.join(home, "Documents", "My Kindle Content")
    else:
        return os.path.join(home, "My Kindle Content")


def scan_kindle_files(input_dir: str, ebook_meta_path: str = "ebook-meta") -> list[KindleFile]:
    results: list[KindleFile] = []
    if not os.path.isdir(input_dir):
        return results

    for entry in os.listdir(input_dir):
        entry_path = os.path.join(input_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        if not _PDOC_PATTERN.match(entry):
            continue

        folder_id = entry
        azw_name = f"{folder_id}.azw"
        azw_path = os.path.join(entry_path, azw_name)

        if not os.path.isfile(azw_path):
            continue

        try:
            stat = os.stat(azw_path)
            size = stat.st_size
        except OSError:
            size = 0

        parsed_title = _get_ebook_meta_title(azw_path, ebook_meta_path)

        results.append(KindleFile(
            folder_path=entry_path,
            azw_path=azw_path,
            original_id=folder_id,
            parsed_title=parsed_title,
            size=size,
        ))

    results.sort(key=lambda k: k.display_name.lower())
    return results


def _get_ebook_meta_title(azw_path: str, ebook_meta_path: str = "ebook-meta") -> str:
    try:
        result = subprocess.run(
            [ebook_meta_path, azw_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Title"):
                    title = line.split(":", 1)[1].strip()
                    if title and title != "Unknown":
                        return title
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return ""


def refresh_metadata(kindle_file: KindleFile, ebook_meta_path: str = "ebook-meta"):
    kindle_file.parsed_title = _get_ebook_meta_title(kindle_file.azw_path, ebook_meta_path)
