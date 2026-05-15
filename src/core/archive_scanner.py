from __future__ import annotations

import os
from dataclasses import dataclass, field

from src.utils.helpers import is_archive_file, get_archive_type, format_size


@dataclass
class ArchiveFile:
    path: str
    name: str
    size: int
    archive_type: str
    selected: bool = True

    @property
    def size_display(self) -> str:
        return format_size(self.size)


def scan_archives(input_dir: str) -> list[ArchiveFile]:
    results: list[ArchiveFile] = []
    if not os.path.isdir(input_dir):
        return results

    for root, _dirs, files in os.walk(input_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            if not is_archive_file(fpath):
                continue
            try:
                stat = os.stat(fpath)
            except OSError:
                continue
            results.append(ArchiveFile(
                path=fpath,
                name=fname,
                size=stat.st_size,
                archive_type=get_archive_type(fpath),
            ))

    results.sort(key=lambda a: a.name.lower())
    return results
