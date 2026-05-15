from __future__ import annotations

import os
import re
import shutil


_VOLUME_PATTERNS = [
    r'\s*[-–—]\s*卷\s*\d+.*',
    r'\s*[-–—]\s*第\s*\d+\s*[卷话册部].*',
    r'\s*[-–—]\s*[Vv][Oo][Ll]\.?\s*\d+.*',
    r'\s*[-–—]\s*[Cc][Hh]\.?\s*\d+.*',
    r'\s*[-–—]\s*[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s*\d+.*',
    r'\s*[-–—]\s*[Ee][Pp]\.?\s*\d+.*',
    r'\s*[-–—]\s*[Ss]eason\s*\d+.*',
    r'\s*[-–—]\s*[Pp]art\s*\d+.*',
    r'\s*[-–—]\s*\d+.*',
    r'\s*[Vv][Oo][Ll]\.?\s*\d+.*',
    r'\s*[Vv]\d+.*',
    r'\s*[Cc][Hh]\.?\s*\d+.*',
    r'\s*[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s*\d+.*',
    r'\s*[Ee][Pp]\.?\s*\d+.*',
    r'\s*第\s*\d+\s*[卷话册部].*',
    r'\s*[卷话册部]\s*\d+.*',
    r'\s*\(\s*\d+\s*\).*',
    r'\s*\[\s*\d+\s*\].*',
    r'\s*\d+[卷话册部].*',
    r'\s*\d+(-|到)\d+.*',
    r'\s*\([^)]*[完結完结][^)]*\).*',
    r'\s*\[[^\]]*[完結完结][^\]]*\].*',
    r'\s*[-–—_\s]\d{1,4}\s*$',
    r'\s*#\d+.*',
    r'\s*No\.\s*\d+.*',
    r'\s*[Ss]eason\s*\d+.*',
    r'\s*[Pp]art\s*\d+.*',
    r'\s*[Bb]ook\s*\d+.*',
    r'\s*[Vv]olume\s*\d+.*',
]

_TRAILING_CLEAN = re.compile(r'[-–—_,.\s]+$')


def extract_comic_name(filename_no_ext: str) -> str:
    name = filename_no_ext.strip()
    candidates = [name]
    for pattern in _VOLUME_PATTERNS:
        m = re.search(pattern, name)
        if m:
            candidates.append(_TRAILING_CLEAN.sub('', name[:m.start()].strip()))
    best = name
    for c in candidates:
        if len(c) >= 2 and len(c) < len(best):
            best = c
    return _TRAILING_CLEAN.sub('', best)


def group_comic_files(directory: str, extensions: set[str]) -> dict[str, list[str]]:
    files = []
    for fname in os.listdir(directory):
        fpath = os.path.join(directory, fname)
        if not os.path.isfile(fpath):
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in extensions:
            continue
        files.append(fname)

    groups: dict[str, list[str]] = {}
    for fname in files:
        name_no_ext = os.path.splitext(fname)[0]
        comic_name = extract_comic_name(name_no_ext)
        groups.setdefault(comic_name, []).append(fname)

    return {k: v for k, v in groups.items() if len(v) > 1}


def organize_comics_into_folders(directory: str, extensions: set[str]) -> int:
    groups = group_comic_files(directory, extensions)
    folder_count = 0
    for comic_name, file_list in groups.items():
        folder_path = os.path.join(directory, comic_name)
        os.makedirs(folder_path, exist_ok=True)
        for fname in file_list:
            src = os.path.join(directory, fname)
            dst = os.path.join(folder_path, fname)
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.move(src, dst)
        folder_count += 1
    return folder_count
