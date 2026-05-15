from __future__ import annotations

import os

from PySide6.QtCore import QSettings

SETTINGS_ORG = "ComicBinder"
SETTINGS_APP = "ComicBinder"


def _settings() -> QSettings:
    return QSettings(SETTINGS_ORG, SETTINGS_APP)


def get_last_path(key: str, default: str = "") -> str:
    val = _settings().value(key, default)
    if val and os.path.exists(str(val)):
        return str(val)
    return default


def set_last_path(key: str, path: str):
    _settings().setValue(key, path)


def get_calibre_path() -> str:
    val = _settings().value("calibre/install_path", "")
    if val:
        p = str(val)
        if os.path.exists(p):
            return p
    # auto-detect
    for candidate in [
        r"C:\Program Files\Calibre2",
        r"C:\Program Files (x86)\Calibre2",
        r"/Applications/calibre.app/Contents/MacOS",
        r"/usr/bin",
    ]:
        if os.path.isdir(candidate):
            return candidate
    return ""


def set_calibre_path(path: str):
    _settings().setValue("calibre/install_path", path)


def get_ebook_meta_path() -> str:
    calibre = get_calibre_path()
    if not calibre:
        return "ebook-meta"
    exe = os.path.join(calibre, "ebook-meta.exe")
    if os.path.isfile(exe):
        return exe
    exe2 = os.path.join(calibre, "ebook-meta")
    if os.path.isfile(exe2):
        return exe2
    return "ebook-meta"


def get_ebook_convert_path() -> str:
    calibre = get_calibre_path()
    if not calibre:
        return "ebook-convert"
    exe = os.path.join(calibre, "ebook-convert.exe")
    if os.path.isfile(exe):
        return exe
    exe2 = os.path.join(calibre, "ebook-convert")
    if os.path.isfile(exe2):
        return exe2
    return "ebook-convert"
