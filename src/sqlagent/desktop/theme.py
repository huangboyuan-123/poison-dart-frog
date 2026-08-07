"""
暗色主题 Stylesheet
"""

DARK_QSS = """
QMainWindow, QWidget { background: #2B2B2B; color: #A9B7C6; font-family: "JetBrains Mono","Consolas","Microsoft YaHei"; font-size: 13px; }
QGroupBox { border: 1px solid rgba(255,255,255,0.06); border-radius: 4px; margin-top: 14px; padding-top: 14px; font-weight: bold; color: #86909C; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }
QLineEdit, QPlainTextEdit, QTextEdit {
    background: #3C3F41; color: #A9B7C6; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 4px; padding: 6px 8px; selection-background-color: #8B3A3A;
}
QPlainTextEdit:focus, QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #8B3A3A;
}
QComboBox {
    background: #3C3F41; color: #A9B7C6; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 4px; padding: 4px 8px; min-height: 20px;
}
QComboBox:hover { border-color: rgba(255,255,255,0.12); }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #3C3F41; color: #A9B7C6; selection-background-color: #8B3A3A;
    border: 1px solid rgba(255,255,255,0.06); outline: none;
}
QPushButton {
    background: #3C3F41; color: #A9B7C6; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 4px; padding: 5px 14px; min-height: 26px;
}
QPushButton:hover { background: #4E5254; border-color: rgba(255,255,255,0.15); }
QPushButton:pressed { background: #8B3A3A; }
QPushButton[accent="true"] { background: #8B3A3A; border: none; font-weight: bold; }
QPushButton[accent="true"]:hover { background: #00897B; }
QPushButton[danger="true"] { background: #E05555; border: none; }
QPushButton:disabled { background: #3C3F41; color: #5A6270; }
QTableWidget {
    background: #3C3F41; color: #A9B7C6; gridline-color: rgba(255,255,255,0.04);
    border: none; selection-background-color: #8B3A3A;
}
QTableWidget::item { padding: 2px 6px; }
QHeaderView::section {
    background: #3C3F41; color: #86909C; border: none; border-bottom: 2px solid rgba(255,255,255,0.06);
    padding: 4px 8px; font-weight: bold; font-size: 11px;
}
QTabWidget::pane { border: none; background: #2B2B2B; }
QTabBar::tab {
    background: #3C3F41; color: #86909C; border: none; padding: 6px 24px 6px 12px;
    margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px;
}
QTabBar::tab:selected { background: #8B3A3A; color: #A9B7C6; }
QTabBar::tab:hover:!selected { background: #4E5254; }
QSplitter::handle { background: rgba(255,255,255,0.04); }
QSplitter::handle:hover { background: #8B3A3A; }
QScrollBar:vertical { background: #2B2B2B; width: 6px; }
QScrollBar::handle:vertical { background: #5A6270; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #86909C; }
QScrollBar:horizontal { background: #2B2B2B; height: 6px; }
QScrollBar::handle:horizontal { background: #5A6270; border-radius: 3px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QStatusBar { background: #2B2B2B; color: #86909C; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px; }
QListWidget { background: #3C3F41; color: #A9B7C6; border: none; outline: none; }
QListWidget::item { padding: 6px 10px; border-bottom: 1px solid rgba(255,255,255,0.03); }
QListWidget::item:hover { background: #4E5254; }
QListWidget::item:selected { background: #8B3A3A; }
QTreeWidget { background: #3C3F41; color: #A9B7C6; border: none; outline: none; }
QTreeWidget::item { padding: 3px 4px; }
QTreeWidget::item:hover { background: #4E5254; }
QTreeWidget::item:selected { background: #8B3A3A; }
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings { border-image: none; }
QCheckBox { color: #86909C; spacing: 6px; }
QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid rgba(255,255,255,0.15); border-radius: 2px; }
QCheckBox::indicator:checked { background: #8B3A3A; border-color: #8B3A3A; }
QDialog { background: #2B2B2B; }
QMenu { background: #3C3F41; color: #A9B7C6; border: 1px solid rgba(255,255,255,0.06); padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 2px; }
QMenu::item:selected { background: #8B3A3A; }
"""
