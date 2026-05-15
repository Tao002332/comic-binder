import sys, os
from PySide6.QtGui import QIcon, QPalette, QColor
from PySide6.QtWidgets import QApplication, QToolTip
from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Comic Binder")

    # Fix tooltip style on Windows
    p = app.palette()
    p.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255, 242))
    p.setColor(QPalette.ColorRole.ToolTipText, QColor("#1c1c1e"))
    app.setPalette(p)

    # Set app icon (taskbar + window)
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)
    icon_path = os.path.join(base, "comic_binder.ico")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    app.setStyleSheet("""
        QMainWindow, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,
        QTableWidget, QHeaderView, QProgressBar, QToolTip {
            font-family: "SF Pro Display", "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
        }

        QMainWindow {
            background-color: #f2f2f7;
        }

        /* ---- Tab Bar ---- */
        QTabWidget::pane {
            border: none;
            background: transparent;
        }
        QTabBar {
            background: rgba(255,255,255,0.72);
            border-radius: 14px;
            padding: 4px;
        }
        QTabBar::tab {
            padding: 9px 24px;
            margin: 2px 2px;
            border: none;
            border-radius: 12px;
            background: transparent;
            color: #8e8e93;
            font-size: 13px;
            font-weight: 540;
        }
        QTabBar::tab:selected {
            background: #ffffff;
            color: #007aff;
            font-weight: 620;
        }
        QTabBar::tab:hover:!selected {
            color: #3c3c43;
        }

        /* ---- Cards (frosted glass) ---- */
        QFrame#glassCard {
            background: rgba(255,255,255,0.72);
            border: 0.5px solid rgba(0,0,0,0.06);
            border-radius: 16px;
        }

        /* ---- Inputs ---- */
        QLineEdit {
            padding: 10px 14px;
            border: 0.5px solid rgba(0,0,0,0.10);
            border-radius: 12px;
            background: rgba(255,255,255,0.80);
            color: #1c1c1e;
            font-size: 14px;
        }
        QLineEdit:focus {
            border-color: #007aff;
            background: #ffffff;
        }
        QLineEdit:placeholder {
            color: #aeaeb2;
        }

        /* ---- Buttons ---- */
        QPushButton {
            padding: 8px 18px;
            border: 0.5px solid rgba(0,0,0,0.10);
            border-radius: 12px;
            background: rgba(255,255,255,0.72);
            color: #3c3c43;
            font-size: 13px;
            font-weight: 520;
        }
        QPushButton:hover {
            background: rgba(255,255,255,0.92);
            border-color: rgba(0,122,255,0.30);
        }
        QPushButton:pressed {
            background: rgba(0,122,255,0.08);
        }
        QPushButton:disabled {
            background: rgba(242,242,247,0.60);
            color: #aeaeb2;
            border-color: transparent;
        }

        QPushButton#primaryBtn {
            background: #007aff;
            color: #ffffff;
            border: none;
            padding: 10px 28px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 14px;
        }
        QPushButton#primaryBtn:hover {
            background: #0066d6;
            color: #ffffff;
        }
        QPushButton#primaryBtn:pressed {
            background: #0055b3;
        }

        /* ---- ComboBox ---- */
        QComboBox {
            padding: 9px 14px;
            border: 0.5px solid rgba(0,0,0,0.10);
            border-radius: 12px;
            background: rgba(255,255,255,0.80);
            color: #1c1c1e;
            font-size: 14px;
            min-width: 100px;
        }
        QComboBox:hover { border-color: rgba(0,122,255,0.30); }
        QComboBox::drop-down { border: none; width: 28px; subcontrol-position: right center; }
        QComboBox QAbstractItemView {
            border-radius: 12px;
            background: rgba(255,255,255,0.95);
            selection-background-color: rgba(0,122,255,0.12);
            selection-color: #007aff;
        }

        /* ---- CheckBox (global, mostly handled by AnimatedCheckBox) ---- */
        QCheckBox {
            spacing: 8px;
            color: #3c3c43;
        }

        /* ---- Scrollbars ---- */
        QScrollArea { border: none; background: transparent; }
        QScrollBar:vertical {
            border: none; background: transparent; width: 5px; margin: 4px 0;
        }
        QScrollBar::handle:vertical {
            background: rgba(0,0,0,0.15); border-radius: 3px; min-height: 30px;
        }
        QScrollBar::handle:vertical:hover { background: rgba(0,0,0,0.25); }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal {
            border: none; background: transparent; height: 5px; margin: 0 4px;
        }
        QScrollBar::handle:horizontal {
            background: rgba(0,0,0,0.15); border-radius: 3px; min-width: 30px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

        /* ---- Progress Bars ---- */
        QProgressBar {
            border: none;
            border-radius: 6px;
            background: rgba(0,0,0,0.06);
            text-align: center;
            font-size: 10px;
            color: #8e8e93;
            height: 6px;
        }
        QProgressBar::chunk {
            border-radius: 6px;
            background: #007aff;
        }

    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
