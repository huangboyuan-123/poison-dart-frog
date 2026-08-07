"""
SQLAgent Desktop — PySide6 桌面端
Qt for Python 现代 GUI

This file is kept for backward compatibility.
All code has been refactored into the sqlagent.desktop package.
"""
from sqlagent.desktop.main import main
from sqlagent.desktop.main_window import MainWindow
from sqlagent.desktop.constants import (
    API_BASE, ICONS_DIR, BG, PANEL, INPUT_BG, MUTED,
    SUCCESS_COLOR, DANGER_COLOR, WARNING_COLOR, ACCENT_COLOR,
    GRADIENT_START, GRADIENT_MID, GRADIENT_END,
    DB_CONFIG_FILE, HISTORY_FILE, DANGER_KW, ENV_FILE,
)
from sqlagent.desktop.theme import DARK_QSS
from sqlagent.desktop.highlighter import SQL_KEYWORDS, SqlHighlighter
from sqlagent.desktop.workers import StreamWorker, ApiWorker
from sqlagent.desktop.utils import _md_to_html, _extract_sql_from_stream, _extract_redis_commands
from sqlagent.desktop.dialogs import DbConfigDialog, SettingsDialog, TableDesignerDialog, _RoundedWidget

if __name__ == '__main__':
    main()
