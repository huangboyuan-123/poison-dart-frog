"""
暗色主题 Stylesheet
"""

DARK_QSS = """
QMainWindow, QWidget { background: #1A1A1D; color: #A9B7C6; font-family: "JetBrains Mono","Consolas","Microsoft YaHei"; font-size: 13px; }
QGroupBox { border: 1px solid rgba(255,255,255,0.06); border-radius: 4px; margin-top: 14px; padding-top: 14px; font-weight: bold; color: #86909C; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }
QLineEdit, QPlainTextEdit, QTextEdit {
    background: rgba(35,35,40,0.95); color: #A9B7C6; border: 1px solid rgba(255,255,255,0.04);
    border-radius: 4px; padding: 6px 8px; selection-background-color: #8B3A3A;
}
QPlainTextEdit:focus, QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #8B3A3A;
}
QComboBox {
    background: rgba(35,35,40,0.95); color: #A9B7C6; border: 1px solid rgba(255,255,255,0.04);
    border-radius: 4px; padding: 4px 8px; min-height: 20px;
}
QComboBox:hover { border-color: rgba(255,255,255,0.12); }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #232328; color: #A9B7C6; selection-background-color: #8B3A3A;
    border: 1px solid rgba(255,255,255,0.06); outline: none;
}
QPushButton {
    background: #28282E; color: #A9B7C6; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 4px; padding: 5px 14px; min-height: 26px;
}
QPushButton:hover { background: #2A2A2A; border-color: rgba(255,255,255,0.15); }
QPushButton:pressed { background: #8B3A3A; }
QPushButton[accent="true"] {
    background: #8B3A3A; border: 2px solid transparent; border-radius: 4px;
    padding: 4px 12px; min-height: 24px; font-weight: bold;
}
QPushButton[accent="true"]:hover { background: #6B2525; }
QPushButton[accent="true"]:pressed { border: 3px solid rgba(139,58,58,0.5); margin: -1px; } border: none; font-weight: bold; }
QPushButton[accent="true"]:hover { background: #00897B; }
QPushButton[danger="true"] { background: #E05555; border: none; }
QPushButton:disabled { background: #232328; color: #5A6270; }
QTableWidget {
    background: #232328; color: #A9B7C6; gridline-color: rgba(255,255,255,0.04);
    border: none; selection-background-color: #8B3A3A;
}
QTableWidget::item { padding: 2px 6px; }
QHeaderView::section {
    background: #232328; color: #86909C; border: none; border-bottom: 2px solid rgba(255,255,255,0.06);
    padding: 4px 8px; font-weight: bold; font-size: 11px;
}
QTabWidget::pane { border: none; background: #1A1A1D; }
QTabBar::tab {
    background: #232328; color: #86909C; border: none; padding: 6px 24px 6px 12px;
    margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px;
}
QTabBar::tab:selected { background: #8B3A3A; color: #A9B7C6; }
QTabBar::tab:hover:!selected { background: #2A2A2A; }
QSplitter::handle { background: rgba(255,255,255,0.04); }
QSplitter::handle:hover { background: #8B3A3A; }
* { scrollbar-width: thin; scrollbar-color: #8B3A3A transparent; }
QScrollBar:vertical { background: transparent; width: 5px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #8B3A3A; border-radius: 3px; min-height: 25px; }
QScrollBar::handle:vertical:hover { background: #A05050; }
QScrollBar::handle:vertical:pressed { background: #6B2525; }
QScrollBar:horizontal { background: transparent; height: 5px; border-radius: 3px; }
QScrollBar::handle:horizontal { background: #8B3A3A; border-radius: 3px; min-width: 25px; }
QScrollBar::handle:horizontal:hover { background: #A05050; }
QScrollBar::handle:horizontal:pressed { background: #6B2525; }
QScrollBar::add-line, QScrollBar::sub-line { background: none; border: none; height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: none; }
QScrollBar::up-arrow, QScrollBar::down-arrow, QScrollBar::left-arrow, QScrollBar::right-arrow { background: none; border: none; }
QStatusBar { background: #1A1A1D; color: #86909C; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px; }
QListWidget { background: #232328; color: #A9B7C6; border: none; outline: none; }
QListWidget::item { padding: 6px 10px; border-bottom: 1px solid rgba(255,255,255,0.03); }
QListWidget::item:hover { background: #2A2A2A; }
QListWidget::item:selected { background: #8B3A3A; }
QTreeWidget { background: #232328; color: #A9B7C6; border: none; outline: none; }
QTreeWidget::item { padding: 3px 4px; }
QTreeWidget::item:hover { background: #2A2A2A; }
QTreeWidget::item:selected { background: #8B3A3A; }
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings { border-image: none; }
QCheckBox { color: #86909C; spacing: 6px; }
QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid rgba(255,255,255,0.15); border-radius: 2px; }
QCheckBox::indicator:checked { background: #8B3A3A; border-color: #8B3A3A; }
QDialog { background: #1A1A1D; }
QMenu { background: rgba(35,35,40,0.95); color: #A9B7C6; border: 1px solid rgba(255,255,255,0.04); padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 2px; }
QMenu::item:selected { background: #8B3A3A; }
"""
