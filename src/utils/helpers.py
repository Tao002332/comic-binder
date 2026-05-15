import os

ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".cbz", ".cbr"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif"}
KINDLE_OUTPUT_FORMATS = ["PDF", "EPUB", "MOBI", "AZW3", "CBZ"]


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_file_extension(path: str) -> str:
    return os.path.splitext(path)[1].lower()


def is_archive_file(path: str) -> bool:
    return get_file_extension(path) in ARCHIVE_EXTENSIONS


def is_image_file(path: str) -> bool:
    return get_file_extension(path) in IMAGE_EXTENSIONS


def get_archive_type(path: str) -> str:
    ext = get_file_extension(path)
    ext_map = {".cbz": "cbz", ".cbr": "cbr"}
    return ext_map.get(ext, ext.lstrip("."))
