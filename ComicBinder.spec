# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('comic_binder.ico', '.')],
    hiddenimports=['src', 'src.core', 'src.core.archive_scanner', 'src.core.archive_converter', 'src.core.kindle_scanner', 'src.core.kindle_converter', 'src.core.task_manager', 'src.ui', 'src.ui.main_window', 'src.ui.archive_tab', 'src.ui.kindle_tab', 'src.ui.widgets', 'src.ui.widgets.file_list_widget', 'src.ui.widgets.progress_widget', 'src.ui.widgets.animated_checkbox', 'src.ui.widgets.custom_tooltip', 'src.utils', 'src.utils.helpers', 'src.utils.settings', 'src.utils.comic_grouper', 'rarfile', 'py7zr', 'natsort', 'img2pdf', 'patoolib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ComicBinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['comic_binder.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ComicBinder',
)
