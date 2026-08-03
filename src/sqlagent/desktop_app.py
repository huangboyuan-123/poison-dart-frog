"""
SQLAgent Desktop — PySide6 桌面端
Qt for Python 现代 GUI
运行: python src/sqlagent/desktop_app.py
"""
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from PySide6 import QtCore
from PySide6.QtCore import (Qt, QThread, Signal, QRect, QRegularExpression, QSize)
from PySide6.QtGui import (QAction, QColor, QFont, QFontDatabase,
                            QKeySequence, QSyntaxHighlighter,
                            QTextCharFormat, QPalette, QIcon, QAction)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox,
                                QDialog, QDialogButtonBox, QFileDialog,
                                QFormLayout, QHBoxLayout, QHeaderView, QLabel,
                                QLineEdit, QMainWindow, QMenu, QMenuBar, QMessageBox,
                                QPlainTextEdit, QPushButton, QSizePolicy,
                                QSpacerItem, QSplitter, QStatusBar, QStyle,
                                QTabWidget, QTableWidget, QTableWidgetItem,
                                QTextEdit, QTreeWidget, QTreeWidgetItem,
                                QVBoxLayout, QWidget, QListWidget,
                                QListWidgetItem, QGroupBox)

# ═══════════════════════════════════════════
# 配色 & 常量
# ═══════════════════════════════════════════
API_BASE = 'http://localhost:8000'
ICONS_DIR = Path(__file__).parent / 'static'
BG = '#1E2128'
MUTED = '#5A6270'
SUCCESS_COLOR = '#3FB950'
DANGER_COLOR = '#E05555'
WARNING_COLOR = '#D29922'
ACCENT_COLOR = '#2574FF'

DB_CONFIG_FILE = Path(__file__).parent.parent.parent / '.db_configs.json'
HISTORY_FILE = Path.home() / '.sqlagent_history.json'

DANGER_KW = ['DROP TABLE', 'DROP DATABASE', 'TRUNCATE', 'DELETE FROM']

# ═══════════════════════════════════════════
# 暗色主题 Stylesheet
# ═══════════════════════════════════════════
DARK_QSS = """
QMainWindow, QWidget { background: #1E2128; color: #E8E8E8; font-family: "Consolas","Microsoft YaHei"; font-size: 13px; }
QGroupBox { border: 1px solid rgba(255,255,255,0.06); border-radius: 4px; margin-top: 14px; padding-top: 14px; font-weight: bold; color: #86909C; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }
QLineEdit, QPlainTextEdit, QTextEdit {
    background: #2F343D; color: #E8E8E8; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 4px; padding: 6px 8px; selection-background-color: #2574FF;
}
QPlainTextEdit:focus, QTextEdit:focus, QLineEdit:focus {
    border: 1px solid #2574FF;
}
QComboBox {
    background: #2F343D; color: #E8E8E8; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 4px; padding: 4px 8px; min-height: 20px;
}
QComboBox:hover { border-color: rgba(255,255,255,0.12); }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background: #272B33; color: #E8E8E8; selection-background-color: #2574FF;
    border: 1px solid rgba(255,255,255,0.06); outline: none;
}
QPushButton {
    background: #2F343D; color: #E8E8E8; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 4px; padding: 5px 14px; min-height: 26px;
}
QPushButton:hover { background: #363B44; border-color: rgba(255,255,255,0.15); }
QPushButton:pressed { background: #2574FF; }
QPushButton[accent="true"] { background: #2574FF; border: none; font-weight: bold; }
QPushButton[accent="true"]:hover { background: #1A5FD4; }
QPushButton[danger="true"] { background: #E05555; border: none; }
QPushButton:disabled { background: #2F343D; color: #5A6270; }
QTableWidget {
    background: #272B33; color: #E8E8E8; gridline-color: rgba(255,255,255,0.04);
    border: none; selection-background-color: #2574FF;
}
QTableWidget::item { padding: 2px 6px; }
QHeaderView::section {
    background: #2F343D; color: #86909C; border: none; border-bottom: 2px solid rgba(255,255,255,0.06);
    padding: 4px 8px; font-weight: bold; font-size: 11px;
}
QTabWidget::pane { border: none; background: #1E2128; }
QTabBar::tab {
    background: #272B33; color: #86909C; border: none; padding: 6px 16px;
    margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px;
}
QTabBar::tab:selected { background: #2574FF; color: #E8E8E8; }
QTabBar::tab:hover:!selected { background: #363B44; }
QSplitter::handle { background: rgba(255,255,255,0.04); }
QSplitter::handle:hover { background: #2574FF; }
QScrollBar:vertical { background: #1E2128; width: 6px; }
QScrollBar::handle:vertical { background: #5A6270; border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #86909C; }
QScrollBar:horizontal { background: #1E2128; height: 6px; }
QScrollBar::handle:horizontal { background: #5A6270; border-radius: 3px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QStatusBar { background: #1E2128; color: #86909C; border-top: 1px solid rgba(255,255,255,0.06); font-size: 11px; }
QListWidget { background: #272B33; color: #E8E8E8; border: none; outline: none; }
QListWidget::item { padding: 6px 10px; border-bottom: 1px solid rgba(255,255,255,0.03); }
QListWidget::item:hover { background: #363B44; }
QListWidget::item:selected { background: #2574FF; }
QTreeWidget { background: #272B33; color: #E8E8E8; border: none; outline: none; }
QTreeWidget::item { padding: 3px 4px; }
QTreeWidget::item:hover { background: #363B44; }
QTreeWidget::item:selected { background: #2574FF; }
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings { border-image: none; }
QCheckBox { color: #86909C; spacing: 6px; }
QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid rgba(255,255,255,0.15); border-radius: 2px; }
QCheckBox::indicator:checked { background: #2574FF; border-color: #2574FF; }
QDialog { background: #1E2128; }
QMenu { background: #272B33; color: #E8E8E8; border: 1px solid rgba(255,255,255,0.06); padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 2px; }
QMenu::item:selected { background: #2574FF; }
"""

# ═══════════════════════════════════════════
# SQL 语法高亮器
# ═══════════════════════════════════════════
SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
    'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS', 'GROUP', 'BY',
    'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'INSERT', 'INTO',
    'VALUES', 'UPDATE', 'SET', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TABLE',
    'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'EXPLAIN', 'INDEX',
    'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'NULL', 'DEFAULT',
    'AUTO_INCREMENT', 'CASCADE', 'INFORMATION_SCHEMA', 'TABLE_NAME',
    'COLUMN_NAME', 'DATE_SUB', 'DATE_ADD', 'NOW', 'VARCHAR', 'INT',
    'BIGINT', 'DECIMAL', 'TEXT', 'DATETIME', 'TIMESTAMP', 'IF', 'EXISTS',
    'SHOW', 'DESCRIBE', 'USE', 'TRUNCATE', 'RENAME', 'REPLACE', 'MERGE',
    'ASC', 'DESC', 'IS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'ALL',
    'ANY', 'SOME', 'FULL', 'CROSS', 'NATURAL', 'USING', 'UNIQUE', 'CHECK',
    'CONSTRAINT', 'ADD', 'COLUMN', 'MODIFY', 'CHANGE', 'RENAME', 'TO',
    'GRANT', 'REVOKE', 'ON', 'SCHEMA', 'DATABASE', 'VIEW', 'PROCEDURE',
    'FUNCTION', 'TRIGGER', 'EVENT', 'CHARACTER', 'COLLATE', 'ENGINE',
    'INNODB', 'MYISAM', 'CHARSET', 'UTF8MB4',
]

class SqlHighlighter(QSyntaxHighlighter):
    """SQL 语法高亮器"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: List[tuple] = []

        # 关键字 (蓝色加粗)
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor('#6CB6FF'))
        kw_fmt.setFontWeight(QFont.Bold)
        for kw in SQL_KEYWORDS:
            pattern = QRegularExpression(
                r'\b' + kw.replace(' ', r'\s+') + r'\b',
                QRegularExpression.CaseInsensitiveOption
            )
            self.rules.append((pattern, kw_fmt))

        # 字符串 (绿色)
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor('#96D0A0'))
        self.rules.append((QRegularExpression(r"'[^']*'"), str_fmt))
        self.rules.append((QRegularExpression(r'"[^"]*"'), str_fmt))

        # 数字 (橙色)
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor('#F0B679'))
        self.rules.append((QRegularExpression(r'\b\d+\.?\d*\b'), num_fmt))

        # 注释 (灰色斜体)
        cmt_fmt = QTextCharFormat()
        cmt_fmt.setForeground(QColor(MUTED))
        cmt_fmt.setFontItalic(True)
        self.rules.append((QRegularExpression(r'--[^\n]*'), cmt_fmt))
        self.rules.append((QRegularExpression(r'/\*.*?\*/',
                           QRegularExpression.DotMatchesEverythingOption), cmt_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ═══════════════════════════════════════════
# 后台工作线程
# ═══════════════════════════════════════════
class ApiWorker(QThread):
    """后台 API 调用线程"""
    finished = Signal(object)

    def __init__(self, target, *args):
        super().__init__()
        self._target = target
        self._args = args

    def run(self):
        try:
            result = self._target(*self._args)
        except Exception as e:
            result = {'error': str(e), 'success': False}
        self.finished.emit(result)


# ═══════════════════════════════════════════
# 数据库配置存储
# ═══════════════════════════════════════════
_db_configs: List[Dict[str, Any]] = []

def load_db_configs():
    global _db_configs
    try:
        if DB_CONFIG_FILE.exists():
            _db_configs = json.loads(DB_CONFIG_FILE.read_text('utf-8'))
    except Exception:
        _db_configs = []

def save_db_configs():
    DB_CONFIG_FILE.write_text(json.dumps(_db_configs, ensure_ascii=False, indent=2), 'utf-8')

def load_history() -> List[Dict]:
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text('utf-8'))
    except Exception:
        pass
    return []

def save_history(items: List[Dict]):
    HISTORY_FILE.write_text(json.dumps(items[-200:], ensure_ascii=False, indent=2), 'utf-8')


# ═══════════════════════════════════════════
# DB 连接弹窗
# ═══════════════════════════════════════════
class DbConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('数据库连接配置')
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        layout.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('我的数据库')
        layout.addRow('名称:', self.name_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(['mysql', 'postgresql', 'sqlserver', 'sqlite'])
        layout.addRow('类型:', self.type_combo)

        self.host_edit = QLineEdit('localhost')
        layout.addRow('地址:', self.host_edit)

        self.port_edit = QLineEdit('3306')
        layout.addRow('端口:', self.port_edit)

        self.user_edit = QLineEdit('root')
        layout.addRow('用户名:', self.user_edit)

        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        layout.addRow('密码:', self.pass_edit)

        self.db_edit = QLineEdit('')
        layout.addRow('数据库:', self.db_edit)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def get_config(self) -> Dict[str, Any]:
        return {
            'id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'name': self.name_edit.text(),
            'type': self.type_combo.currentText(),
            'host': self.host_edit.text(),
            'port': int(self.port_edit.text()) if self.port_edit.text().isdigit() else 3306,
            'user': self.user_edit.text(),
            'password': self.pass_edit.text(),
            'database': self.db_edit.text(),
        }


# ═══════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SQLAgent Desktop')
        self.resize(1200, 780)
        self.setMinimumSize(900, 600)

        self.PAGE_SIZE = 100
        self._current_db: Optional[Dict] = None
        self._c_collapsed = False
        self._c_saved_width = 0

        self._setup_ui()
        self._load_data()

    # ── UI 构建 ────────────────────────────
    def _setup_ui(self):
        # ── 菜单栏 ──
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{ background: {BG}; color: {MUTED}; border-bottom: 1px solid rgba(255,255,255,0.06); padding: 2px 0; }}
            QMenuBar::item {{ padding: 4px 12px; }}
            QMenuBar::item:selected {{ background: {ACCENT_COLOR}; color: white; }}
        """)

        file_menu = menubar.addMenu('文件')
        act_conn = QAction('编辑连接', self)
        act_conn.triggered.connect(self._add_db_dialog)
        file_menu.addAction(act_conn)
        file_menu.addSeparator()
        act_exit = QAction('退出', self)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        tools_menu = menubar.addMenu('工具')
        act_export_csv = QAction('导出 CSV', self)
        act_export_csv.triggered.connect(self._export_csv)
        tools_menu.addAction(act_export_csv)
        tools_menu.addSeparator()
        act_clear_hist = QAction('清除历史记录', self)
        act_clear_hist.triggered.connect(self._clear_history)
        tools_menu.addAction(act_clear_hist)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 三栏分栏: A(表树) | B(数据浏览) | C(AI+日志)
        splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(splitter)

        panel_a = QWidget()
        panel_b = QWidget()
        panel_c = QWidget()
        self.panel_c = panel_c  # 保存引用用于折叠
        splitter.addWidget(panel_a)
        splitter.addWidget(panel_b)
        splitter.addWidget(panel_c)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 40)
        splitter.setStretchFactor(2, 60)
        splitter.setHandleWidth(4)
        panel_a.setFixedWidth(200)

        self._build_panel_a(panel_a)
        self._build_panel_b(panel_b)
        self._build_panel_c(panel_c)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.sb_db = QLabel('● 检测中...')
        self.sb_history = QLabel('')
        self.status_bar.addWidget(self.sb_db)
        self.status_bar.addPermanentWidget(self.sb_history)

    # ═══ A栏: 数据库菜单 ═══
    def _build_panel_a(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(4, 8, 2, 4)
        layout.setSpacing(4)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel('📊 数据库'))
        hdr.addStretch()
        add_btn = QPushButton('+ 新增')
        add_btn.setFixedHeight(22)
        add_btn.clicked.connect(self._add_db_dialog)
        hdr.addWidget(add_btn)
        refresh_btn = QPushButton('刷新')
        refresh_btn.setFixedHeight(22)
        refresh_btn.clicked.connect(self._load_schema_tree)
        hdr.addWidget(refresh_btn)
        layout.addLayout(hdr)

        self.schema_tree = QTreeWidget()
        self.schema_tree.setHeaderHidden(True)
        self.schema_tree.setIndentation(14)
        self.schema_tree.setIconSize(QSize(18, 18))
        self.schema_tree.itemExpanded.connect(self._on_tree_expand)
        self.schema_tree.itemClicked.connect(self._on_tree_click)
        self.schema_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.schema_tree.customContextMenuRequested.connect(self._on_tree_menu)
        layout.addWidget(self.schema_tree, 1)

        self.tree_label = QLabel('')
        self.tree_label.setStyleSheet(f'color: {MUTED}; font-size: 10px;')
        layout.addWidget(self.tree_label)

        conn_row = QHBoxLayout()
        self.sidebar_combo = QComboBox()
        self.sidebar_combo.setMinimumHeight(24)
        self.sidebar_combo.currentIndexChanged.connect(self._on_sidebar_db_select)
        conn_row.addWidget(self.sidebar_combo, 1)
        mgr_btn = QPushButton('⚙')
        mgr_btn.setFixedSize(22, 22)
        mgr_btn.setToolTip('管理连接')
        mgr_btn.clicked.connect(self._add_db_dialog)
        conn_row.addWidget(mgr_btn)
        layout.addLayout(conn_row)

    # ═══ B栏: 数据浏览器 (多Tab) ═══
    def _build_panel_b(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(2, 4, 4, 4)
        layout.setSpacing(2)

        # 顶部状态行
        top = QHBoxLayout()
        self.rb_type = QLabel('')
        self.rb_elapsed = QLabel('')
        self.rb_rows = QLabel('')
        for lbl in [self.rb_type, self.rb_elapsed, self.rb_rows]:
            lbl.setStyleSheet(f'color: {MUTED}; font-size: 11px;')
            top.addWidget(lbl)
        self.rb_status = QLabel('')
        top.addWidget(self.rb_status)
        top.addStretch()
        self.expand_btn = QPushButton('▶ 展开AI')
        self.expand_btn.setFixedHeight(20)
        self.expand_btn.clicked.connect(self._toggle_panel_c)
        self.expand_btn.hide()
        top.addWidget(self.expand_btn)
        layout.addLayout(top)

        # 可关闭的 Tab 容器
        self.data_tabs = QTabWidget()
        self.data_tabs.setTabsClosable(True)
        self.data_tabs.tabCloseRequested.connect(self._close_data_tab)
        self.data_tabs.currentChanged.connect(self._on_tab_changed)
        self.data_tabs.setMovable(True)
        layout.addWidget(self.data_tabs, 1)

        # 编辑工具栏
        edit_bar = QHBoxLayout()
        self.save_btn = QPushButton('💾 保存修改')
        self.save_btn.setFixedHeight(24)
        self.save_btn.setProperty('accent', True)
        self.save_btn.clicked.connect(self._save_edits)
        self.save_btn.setEnabled(False)
        edit_bar.addWidget(self.save_btn)
        self.undo_btn = QPushButton('↩ 撤销')
        self.undo_btn.setFixedHeight(24)
        self.undo_btn.clicked.connect(self._undo_edits)
        self.undo_btn.setEnabled(False)
        edit_bar.addWidget(self.undo_btn)
        edit_bar.addStretch()
        add_btn = QPushButton('+ 新增行')
        add_btn.setFixedHeight(24)
        add_btn.clicked.connect(self._add_row_dialog)
        edit_bar.addWidget(add_btn)
        del_btn = QPushButton('🗑 删除行')
        del_btn.setFixedHeight(24)
        del_btn.clicked.connect(self._delete_selected_row)
        edit_bar.addWidget(del_btn)
        layout.addLayout(edit_bar)

        # 编辑跟踪
        self._edits: Dict[str, str] = {}  # key: "row_col" → new_value
        self._current_pk_col = ''
        self._current_db = ''

        # 翻页
        pager = QHBoxLayout()
        self.page_label = QLabel('')
        self.page_label.setStyleSheet(f'color: {MUTED}; font-size: 11px;')
        pager.addWidget(self.page_label)
        pager.addStretch()
        pb1 = QPushButton('← 上一页')
        pb1.setFixedHeight(24)
        pb1.clicked.connect(self._prev_page)
        pager.addWidget(pb1)
        pb2 = QPushButton('下一页 →')
        pb2.setFixedHeight(24)
        pb2.clicked.connect(self._next_page)
        pager.addWidget(pb2)
        layout.addLayout(pager)

        # Tab 数据存储: {tab_index: {'title','rows','columns','page','sql'}}
        self._tab_data: Dict[int, Dict] = {}
        self._add_data_tab('📋 欢迎', [], ['提示'], is_temp=True)
        tbl = self._current_table()
        if tbl:
            tbl.setRowCount(1)
            item = QTableWidgetItem('👈 点击左侧表名 或 在右侧执行SQL')
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            tbl.setItem(0, 0, item)

    # ═══ C栏: AI助手 + 日志 ═══
    def _build_panel_c(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(4, 4, 8, 4)
        layout.setSpacing(6)

        # 折叠按钮
        toggle_row = QHBoxLayout()
        toggle_row.addStretch()
        self.collapse_btn = QPushButton('◀ 隐藏AI')
        self.collapse_btn.setFixedHeight(20)
        self.collapse_btn.clicked.connect(self._toggle_panel_c)
        toggle_row.addWidget(self.collapse_btn)
        layout.addLayout(toggle_row)

        # DB 配置
        db_bar = QHBoxLayout()
        self.db_combo = QComboBox()
        self.db_combo.setMinimumHeight(26)
        self.db_combo.currentIndexChanged.connect(self._on_db_select)
        db_bar.addWidget(self.db_combo, 1)
        self.db_status = QLabel('')
        self.db_status.setStyleSheet(f'color: {MUTED}; font-size: 11px;')
        db_bar.addWidget(self.db_status)
        layout.addLayout(db_bar)

        # 自然语言输入
        nl_group = QGroupBox('自然语言输入')
        nl_ly = QVBoxLayout(nl_group)
        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText('用中文描述想要查询/修改的数据...\n例: 查询本月订单总数')
        self.input_text.setMaximumHeight(100)
        nl_ly.addWidget(self.input_text)
        btn_row = QHBoxLayout()
        self.gen_btn = QPushButton('生成 SQL')
        self.gen_btn.setProperty('accent', True)
        self.gen_btn.clicked.connect(self._generate_sql)
        btn_row.addWidget(self.gen_btn)
        btn_row.addWidget(QPushButton('清空', clicked=lambda: self.input_text.clear()))
        btn_row.addStretch()
        nl_ly.addLayout(btn_row)
        layout.addWidget(nl_group)

        # SQL 预览
        sql_group = QGroupBox('SQL 预览')
        sql_ly = QVBoxLayout(sql_group)
        self.sql_text = QPlainTextEdit()
        self.sql_text.setPlaceholderText('-- AI 生成的 SQL 将显示在这里')
        self.sql_text.setReadOnly(True)
        self.sql_text.setLineWrapMode(QPlainTextEdit.NoWrap)
        font = QFont('Consolas', 10)
        font.setStyleHint(QFont.Monospace)
        self.sql_text.setFont(font)
        sql_ly.addWidget(self.sql_text)
        self.highlighter = SqlHighlighter(self.sql_text.document())

        exec_row = QHBoxLayout()
        self.exec_btn = QPushButton('执行 SQL')
        self.exec_btn.setProperty('accent', True)
        self.exec_btn.clicked.connect(self._execute_sql)
        exec_row.addWidget(self.exec_btn)
        exec_row.addWidget(QPushButton('导出 CSV', clicked=self._export_csv))
        self.tx_check = QCheckBox('开启事务')
        exec_row.addWidget(self.tx_check)
        exec_row.addStretch()
        exec_row.addWidget(QPushButton('复制 SQL', clicked=self._copy_sql))
        sql_ly.addLayout(exec_row)
        layout.addWidget(sql_group, 1)

        # 日志 + 历史 (tabs)
        self.tabs = QTabWidget()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Consolas', 10))
        self.tabs.addTab(self.log_text, '执行日志')
        self._show_log('AI 生成的 SQL 分析、执行日志将显示在这里')

        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_click)
        self.tabs.addTab(self.history_list, '历史记录')
        layout.addWidget(self.tabs)

    # ── 数据加载 ────────────────────────────
    def _load_data(self):
        load_db_configs()
        self._refresh_db_combo()
        self._refresh_history()
        self._check_health()
        self._load_schema_tree()

    def _refresh_db_combo(self):
        self.db_combo.clear()
        self.sidebar_combo.clear()
        for c in _db_configs:
            label = f"{c['name']} ({c['type']})"
            self.db_combo.addItem(label, c)
            self.sidebar_combo.addItem(label, c)
        if _db_configs:
            self._current_db = _db_configs[0]
            self.sidebar_combo.setCurrentIndex(0)

    def _on_db_select(self, idx):
        if 0 <= idx < len(_db_configs):
            self._current_db = _db_configs[idx]
            self._load_schema_tree()

    def _on_sidebar_db_select(self, idx):
        """侧边栏连接切换 — 同步到主面板"""
        if 0 <= idx < len(_db_configs):
            self._current_db = _db_configs[idx]
            self.db_combo.setCurrentIndex(idx)
            self._load_schema_tree()

    # ── Schema 树 ────────────────────────────
    def _load_schema_tree(self):
        """加载所有数据库 → 表 → 列 到树控件"""
        self.schema_tree.clear()
        self.tree_label.setText('加载中...')

        def do_fetch():
            try:
                r = requests.get(f'{API_BASE}/api/databases', timeout=10)
                return r.json()
            except Exception as e:
                return {'error': str(e)}

        def callback(data):
            if 'error' in data:
                self.tree_label.setText('加载失败')
                return

            dbs = data.get('databases', [])
            self.tree_label.setText(f'{len(dbs)} 个数据库')

            for db_name in dbs:
                db_item = QTreeWidgetItem([db_name])
                db_icon = QIcon(str(ICONS_DIR / 'database.png'))
                db_item.setIcon(0, db_icon)
                db_item.setData(0, Qt.UserRole + 1, 'database')
                db_item.setData(0, Qt.UserRole + 2, db_name)
                # 占位符, 展开时加载
                QTreeWidgetItem(db_item, ['...'])
                self.schema_tree.addTopLevelItem(db_item)

        self._run_async(do_fetch, callback)

    def _on_tree_click(self, item: QTreeWidgetItem, _col: int):
        """点击表节点 → B栏加载该表数据"""
        if item.data(0, Qt.UserRole + 1) != 'table':
            return
        table_name = item.text(0)
        db_name = item.data(0, Qt.UserRole + 2)
        self._load_table_data(db_name, table_name)

    def _load_table_data(self, db: str, table: str):
        """加载表数据 → 新建/切换Tab"""
        # 先检查是否已有同名Tab
        title = f'📋 {table}'
        for i in range(self.data_tabs.count()):
            if self.data_tabs.tabText(i) == title:
                self.data_tabs.setCurrentIndex(i)
                return

        def do_fetch():
            try:
                r = requests.post(f'{API_BASE}/api/execute',
                                  json={'sql': f'SELECT * FROM `{db}`.`{table}` LIMIT 500', 'read_only': True},
                                  timeout=30)
                return r.json()
            except Exception as e:
                return {'error': str(e), 'success': False}

        def callback(resp):
            self.rb_type.setText(f'表: {table}')
            self.rb_elapsed.setText('')
            self.rb_status.setText('')
            self.rb_status.setStyleSheet('')
            if resp.get('success') and resp.get('data'):
                data = resp['data']
                # 获取主键列
                pk_col = ''
                try:
                    schema_r = requests.get(f'{API_BASE}/api/schema/{table}?database={db}', timeout=5).json()
                    for col in schema_r.get('columns', []):
                        if col.get('key') == 'PRI':
                            pk_col = col['name']
                            break
                except Exception:
                    pass

                idx = self._add_data_tab(title, data['columns'], data['rows'],
                                         sql=f'SELECT * FROM `{db}`.`{table}`',
                                         db_name=db, pk_col=pk_col)
                self._render_tab_page(idx)
                self.rb_rows.setText(f'{data["row_count"]} 行')
            else:
                err = resp.get('error', '未知错误')
                self.rb_rows.setText('0 行')
                self.rb_status.setText(f'✗ {err}')
                self.rb_status.setStyleSheet(f'color: {DANGER_COLOR}; font-weight: bold;')
                self._show_log(f'✗ 加载表 {table} 失败\n{err}')

        self._run_async(do_fetch, callback)

    # ── 数据 Tab 管理 ──────────────────────
    def _add_data_tab(self, title: str, columns: List[str], rows_data: List[List[Any]] = None,
                      is_temp: bool = False, sql: str = '', db_name: str = '', pk_col: str = ''):
        """新建数据Tab"""
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        # 允许编辑
        table.cellChanged.connect(self._on_cell_edited)

        idx = self.data_tabs.addTab(table, title)
        self.data_tabs.setCurrentIndex(idx)

        info = {'title': title, 'columns': columns, 'rows': rows_data or [],
                'page': 0, 'sql': sql, 'is_temp': is_temp,
                'db_name': db_name, 'table_name': title.replace('📋 ', '').replace('🔍 ', ''),
                'pk_col': pk_col}
        self._tab_data[idx] = info
        if rows_data:
            self._render_tab_page(idx)
        # 更新编辑按钮状态
        self._update_edit_buttons()
        return idx

    def _close_data_tab(self, idx: int):
        """关闭Tab"""
        if self.data_tabs.count() <= 1:
            return
        # 重建 tab_data 映射
        old_keys = list(self._tab_data.keys())
        self.data_tabs.removeTab(idx)
        new_data = {}
        new_idx = 0
        for old_key in old_keys:
            if old_key == idx:
                continue
            new_data[new_idx] = self._tab_data[old_key]
            new_idx += 1
        self._tab_data = new_data

    def _current_table(self) -> QTableWidget:
        """获取当前Tab的表格"""
        w = self.data_tabs.currentWidget()
        return w if isinstance(w, QTableWidget) else None

    def _current_tab_info(self) -> Dict:
        """获取当前Tab信息"""
        return self._tab_data.get(self.data_tabs.currentIndex(),
                                  {'rows': [], 'page': 0, 'columns': [], 'title': '', 'sql': '', 'is_temp': False})

    # ── 单元格编辑 ─────────────────────────
    def _on_cell_edited(self, row: int, col: int):
        """单元格被编辑时记录修改"""
        tbl = self._current_table()
        if not tbl:
            return
        info = self._current_tab_info()
        rows = info.get('rows', [])
        if row >= len(rows) or col >= len(rows[row]):
            return
        # 原始值
        orig = rows[row][col]
        orig_str = '' if orig is None else str(orig)
        new_val = tbl.item(row, col).text() if tbl.item(row, col) else ''
        # 只记录实际变更
        if new_val != orig_str:
            key = f'{row}_{col}'
            self._edits[key] = new_val
        elif f'{row}_{col}' in self._edits:
            del self._edits[f'{row}_{col}']
        self._update_edit_buttons()

    def _update_edit_buttons(self):
        has_edits = bool(self._edits)
        self.save_btn.setEnabled(has_edits)
        self.undo_btn.setEnabled(has_edits)
        if has_edits:
            self.save_btn.setText(f'💾 保存 ({len(self._edits)})')
        else:
            self.save_btn.setText('💾 保存修改')

    def _undo_edits(self):
        """撤销所有编辑"""
        for key in list(self._edits.keys()):
            row_str, col_str = key.split('_')
            r, c = int(row_str), int(col_str)
            info = self._current_tab_info()
            rows = info.get('rows', [])
            if r < len(rows) and c < len(rows[r]):
                tbl = self._current_table()
                if tbl and tbl.item(r, c):
                    orig = rows[r][c]
                    tbl.item(r, c).setText('' if orig is None else str(orig))
                    if orig is None:
                        tbl.item(r, c).setForeground(QColor(MUTED))
        self._edits.clear()
        self._update_edit_buttons()

    def _save_edits(self):
        """保存所有修改到数据库"""
        if not self._edits:
            return
        info = self._current_tab_info()
        db_name = info.get('db_name', '')
        table_name = info.get('table_name', '')
        pk_col = info.get('pk_col', '')
        rows = info.get('rows', [])

        if not db_name or not table_name:
            # 尝试从 tab 标题推断
            title = info.get('title', '')
            # 标题格式: "📋 users" 但 db_name 应该在 _load_table_data 中传入
            QMessageBox.warning(self, '提示', '无法确定数据库名，请先刷新表数据')
            return

        if not pk_col:
            pk_col = info.get('columns', ['id'])[0]  # 默认第一列是主键

        saved = 0
        errors = []
        for key, new_val in self._edits.items():
            row_str, col_str = key.split('_')
            r, c = int(row_str), int(col_str)
            if r >= len(rows):
                continue
            col_name = info['columns'][c] if c < len(info.get('columns', [])) else f'col_{c}'
            pk_val = str(rows[r][info['columns'].index(pk_col)]) if pk_col in info.get('columns', []) else str(r)

            try:
                resp = requests.post(f'{API_BASE}/api/table/update', json={
                    'database': db_name, 'table': table_name,
                    'pk_column': pk_col, 'pk_value': pk_val,
                    'column': col_name, 'value': new_val,
                }, timeout=10).json()
                if resp.get('success'):
                    saved += 1
                    # 更新本地缓存
                    rows[r][c] = new_val
                else:
                    errors.append(f'{col_name}: {resp.get("detail", "失败")}')
            except Exception as e:
                errors.append(f'{col_name}: {e}')

        self._edits.clear()
        self._update_edit_buttons()
        if errors:
            self.rb_status.setText(f'✗ {len(errors)} 个失败')
            self.rb_status.setStyleSheet(f'color: {DANGER_COLOR}; font-weight: bold;')
            self._show_log(f'保存结果: {saved} 成功, {len(errors)} 失败\n' + '\n'.join(errors))
        else:
            self.rb_status.setText(f'✓ 已保存 {saved} 处修改')
            self.rb_status.setStyleSheet(f'color: {SUCCESS_COLOR}; font-weight: bold;')
            self._render_tab_page()

    def _add_row_dialog(self):
        """新增行弹窗"""
        info = self._current_tab_info()
        if info.get('is_temp'):
            QMessageBox.warning(self, '提示', '请先打开一个数据表')
            return
        cols = info.get('columns', [])
        if not cols:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle('新增行')
        dialog.setMinimumWidth(360)
        layout = QFormLayout(dialog)
        entries = {}
        for col in cols:
            e = QLineEdit()
            entries[col] = e
            layout.addRow(col, e)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(lambda: self._do_insert(info, entries, dialog))
        btns.rejected.connect(dialog.reject)
        layout.addRow(btns)
        dialog.exec()

    def _do_insert(self, info: Dict, entries: Dict[str, QLineEdit], dialog: QDialog):
        values = {k: e.text() for k, e in entries.items()}
        db_name = info.get('db_name', '')
        table_name = info.get('table_name', '')
        if not db_name or not table_name:
            return
        try:
            resp = requests.post(f'{API_BASE}/api/table/insert', json={
                'database': db_name, 'table': table_name, 'values': values
            }, timeout=10).json()
            if resp.get('success'):
                dialog.accept()
                self._show_log(f'✓ 已插入 1 行到 {table_name}')
                # 刷新当前 tab
                self._reload_current_tab()
            else:
                QMessageBox.warning(self, '错误', resp.get('detail', '插入失败'))
        except Exception as e:
            QMessageBox.warning(self, '错误', str(e))

    def _delete_selected_row(self):
        """删除选中的行"""
        tbl = self._current_table()
        if not tbl:
            return
        rows = set()
        for item in tbl.selectedItems():
            rows.add(item.row())
        if not rows:
            QMessageBox.warning(self, '提示', '请先点击要删除的行')
            return
        r = list(rows)[0]
        info = self._current_tab_info()
        db_name = info.get('db_name', '')
        table_name = info.get('table_name', '')
        pk_col = info.get('pk_col', info.get('columns', ['id'])[0])
        all_rows = info.get('rows', [])

        if not db_name or not table_name or r >= len(all_rows):
            return
        pk_idx = info['columns'].index(pk_col) if pk_col in info.get('columns', []) else 0
        pk_val = str(all_rows[r][pk_idx])

        if not QMessageBox.question(self, '确认删除',
                                     f'确定删除 {table_name} 中 {pk_col}={pk_val} 的行?'):
            return

        try:
            resp = requests.post(f'{API_BASE}/api/table/delete', json={
                'database': db_name, 'table': table_name,
                'pk_column': pk_col, 'pk_value': pk_val,
            }, timeout=10).json()
            if resp.get('success'):
                self._show_log(f'✓ 已删除 {table_name} 中 {pk_col}={pk_val} 的行')
                self._reload_current_tab()
            else:
                QMessageBox.warning(self, '错误', resp.get('detail', '删除失败'))
        except Exception as e:
            QMessageBox.warning(self, '错误', str(e))

    def _reload_current_tab(self):
        """刷新当前标签页数据"""
        info = self._current_tab_info()
        db_name = info.get('db_name', '')
        table_name = info.get('table_name', '')
        if db_name and table_name:
            self._load_table_data(db_name, table_name)

    def _on_tab_changed(self, idx: int):
        info = self._tab_data.get(idx)
        if info and info.get('rows'):
            self.page_label.setText(
                f'第 {info["page"]+1}/{max(1, (len(info["rows"])+99)//100)} 页 · 共 {len(info["rows"])} 行')

    # ── 折叠 ────────────────────────────────
    def _toggle_panel_c(self):
        """折叠/展开 AI 面板 (C栏)"""
        if self._c_collapsed:
            self.panel_c.setVisible(True)
            self.collapse_btn.setText('◀ 隐藏AI')
            self.expand_btn.hide()
        else:
            self.panel_c.setVisible(False)
            self.collapse_btn.setText('▶')
            self.expand_btn.show()
        self._c_collapsed = not self._c_collapsed

    def _on_tree_expand(self, item: QTreeWidgetItem):
        """展开节点时懒加载"""
        node_type = item.data(0, Qt.UserRole + 1)

        if node_type == 'database':
            # 加载数据库下的表
            item.takeChildren()
            db_name = item.data(0, Qt.UserRole + 2)

            def do_fetch():
                try:
                    r = requests.get(f'{API_BASE}/api/schema?database={db_name}', timeout=10)
                    return r.json()
                except Exception as e:
                    return {'error': str(e)}

            def callback(data):
                if 'error' in data:
                    return
                for t in data.get('tables', []):
                    t_item = QTreeWidgetItem([t['table']])
                    t_item.setData(0, Qt.UserRole + 1, 'table')
                    t_item.setData(0, Qt.UserRole + 2, db_name)
                    t_item.setData(0, Qt.UserRole, t.get('columns', []))
                    QTreeWidgetItem(t_item, ['...'])  # 占位列
                    item.addChild(t_item)

            self._run_async(do_fetch, callback)

        elif node_type == 'table':
            # 加载表的列
            item.takeChildren()
            columns = item.data(0, Qt.UserRole) or []
            for col in columns:
                key_info = ''
                if col.get('key') == 'PRI': key_info = ' 🔑'
                elif col.get('key') == 'MUL': key_info = ' 🔗'
                null = '?' if col.get('nullable') else ''
                col_text = f"{col['name']}: {col['type']}{null}{key_info}"
                col_item = QTreeWidgetItem([col_text])
                col_item.setData(0, Qt.UserRole + 1, 'column')
                col_item.setForeground(0, QColor(MUTED))
                item.addChild(col_item)

    def _on_tree_menu(self, pos):
        """右键菜单"""
        item = self.schema_tree.itemAt(pos)
        if not item:
            return
        node_type = item.data(0, Qt.UserRole + 1)

        if node_type == 'table':
            table_name = item.text(0)
            db_name = item.data(0, Qt.UserRole + 2)
            columns = item.data(0, Qt.UserRole) or []

            menu = QMenu(self)
            act_struct = QAction('查看表结构', self)
            act_struct.triggered.connect(lambda t=table_name, c=columns: self._show_table_structure(t, c))
            menu.addAction(act_struct)

            act_select = QAction(f'SELECT * FROM {table_name}', self)
            act_select.triggered.connect(lambda t=table_name: self.sql_text.setPlainText(
                f'SELECT * FROM {t} LIMIT 100;'))
            menu.addAction(act_select)

            act_design = QAction('设计表 (DDL)', self)
            act_design.triggered.connect(lambda t=table_name, d=db_name: self._show_table_ddl(d, t))
            menu.addAction(act_design)

            act_copy = QAction('复制表名', self)
            act_copy.triggered.connect(lambda t=table_name: QApplication.clipboard().setText(t))
            menu.addAction(act_copy)

            menu.exec(self.schema_tree.mapToGlobal(pos))

        elif node_type == 'database':
            db_name = item.data(0, Qt.UserRole + 2)
            menu = QMenu(self)
            act_use = QAction(f'复制库名', self)
            act_use.triggered.connect(lambda d=db_name: QApplication.clipboard().setText(d))
            menu.addAction(act_use)
            menu.exec(self.schema_tree.mapToGlobal(pos))

    def _show_table_ddl(self, db: str, table: str):
        """显示建表 DDL"""
        def do_fetch():
            try:
                r = requests.get(f'{API_BASE}/api/table/ddl?database={db}&table={table}', timeout=10)
                return r.json()
            except Exception as e:
                return {'error': str(e)}

        def callback(resp):
            if resp.get('ddl'):
                self._show_log(f'-- 建表 DDL: {db}.{table}\n{resp["ddl"]}')
                self.tabs.setCurrentIndex(0)
            else:
                self._show_log(f'✗ 获取DDL失败: {resp.get("detail", "未知错误")}')
                self.tabs.setCurrentIndex(0)

        self._run_async(do_fetch, callback)

    def _show_table_structure(self, table_name: str, columns: list):
        """右键查看表结构 → 新建Tab"""
        rows = [[c.get('name', ''), c.get('type', ''), c.get('key', ''),
                 'YES' if c.get('nullable') else 'NO', str(c.get('default', ''))] for c in columns]
        idx = self._add_data_tab(f'🔍 {table_name}', ['字段', '类型', '键', '可空', '默认值'], rows)
        self._render_tab_page(idx)
        self.rb_type.setText(f'结构: {table_name}')
        self.rb_elapsed.setText('')
        self.rb_rows.setText(f'{len(columns)} 字段')
        self.rb_status.setText('')
        self.rb_status.setStyleSheet('')

    # ── DB 操作 ─────────────────────────────
    def _add_db_dialog(self):
        dlg = DbConfigDialog(self)
        if dlg.exec() == QDialog.Accepted:
            cfg = dlg.get_config()
            if not cfg['name']:
                QMessageBox.warning(self, '提示', '请输入连接名称')
                return
            _db_configs.append(cfg)
            save_db_configs()
            self._refresh_db_combo()

    def _test_db(self):
        if not self._current_db:
            QMessageBox.warning(self, '提示', '请先选择数据库连接')
            return
        self.db_status.setText('检测中...')
        self.db_status.setStyleSheet(f'color: {WARNING_COLOR}; font-size: 11px;')

        def do_test():
            try:
                r = requests.post(f'{API_BASE}/api/execute',
                                  json={'sql': 'SELECT 1', 'read_only': True}, timeout=5)
                return r.json().get('success', False)
            except Exception:
                return False

        def callback(ok):
            if ok:
                self.db_status.setText('✓ 连接成功')
                self.db_status.setStyleSheet(f'color: {SUCCESS_COLOR}; font-size: 11px;')
            else:
                self.db_status.setText('✗ 连接失败')
                self.db_status.setStyleSheet(f'color: {DANGER_COLOR}; font-size: 11px;')

        self._run_async(do_test, callback)

    # ── 生成 SQL ────────────────────────────
    def _generate_sql(self):
        question = self.input_text.toPlainText().strip()
        if not question:
            QMessageBox.warning(self, '提示', '请输入问题')
            return
        self.gen_btn.setText('生成中...')
        self.gen_btn.setEnabled(False)

        def do_generate():
            try:
                # 追加提示确保 AI 返回 SQL
                prompt = question + '\n\n请直接给出SQL语句，不要额外解释。'
                r = requests.post(f'{API_BASE}/api/query',
                                  json={'question': prompt}, timeout=120)
                return r.json()
            except Exception as e:
                return {'error': str(e)}

        def callback(resp):
            self.gen_btn.setText('生成 SQL')
            self.gen_btn.setEnabled(True)
            sql = resp.get('sql', '') or ''
            error = resp.get('error', '') or ''
            answer = resp.get('answer', '') or ''

            if error:
                self.sql_text.setPlainText(f'-- 生成失败: {error}')
                self._show_log(f'✗ 生成失败\n{error}')
                self.tabs.setCurrentIndex(0)
            elif sql and sql.strip():
                # 有提取到的 SQL — 放进预览框
                self.sql_text.setPlainText(sql)
                self._append_log(f'[生成SQL] {question}\n{sql}\n')
            else:
                # 没有 SQL — 只显示 AI 分析在日志区，预览框置灰提示
                self.sql_text.setPlainText('-- AI 未生成 SQL 语句，请查看「执行日志」Tab 中的分析')
                self._show_log(f'🤖 AI 分析 (未生成SQL)\n{"─"*50}\n{answer}')
                self.tabs.setCurrentIndex(0)

        self._run_async(do_generate, callback)

    # ── 执行 SQL ────────────────────────────
    def _execute_sql(self):
        sql = self.sql_text.toPlainText().strip()
        if not sql or sql.startswith('--'):
            return

        # 高危拦截
        upper = sql.upper()
        for kw in DANGER_KW:
            if kw.upper() in upper:
                if kw == 'DELETE FROM' and 'WHERE' in upper:
                    continue
                reply = QMessageBox.question(
                    self, '高危操作',
                    f'检测到高危语句: {kw}\n\n该操作不可逆，确认执行？',
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return

        self.exec_btn.setText('执行中...')
        self.exec_btn.setEnabled(False)
        start = datetime.now()

        def do_execute():
            try:
                is_write = bool(re.match(r'^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)', sql, re.I))
                r = requests.post(f'{API_BASE}/api/execute',
                                  json={'sql': sql, 'read_only': not is_write}, timeout=30)
                data = r.json()
                data['_elapsed'] = (datetime.now() - start).total_seconds() * 1000
                data['_is_write'] = is_write
                return data
            except Exception as e:
                return {'error': str(e), 'success': False,
                        '_elapsed': (datetime.now() - start).total_seconds() * 1000}

        def callback(resp):
            self.exec_btn.setText('执行 SQL')
            self.exec_btn.setEnabled(True)
            elapsed = resp.get('_elapsed', 0)
            is_write = resp.get('_is_write', False)

            sql_type = 'SELECT'
            if is_write:
                sql_type = sql.strip().split()[0].upper()
            self.rb_type.setText(f'类型: {sql_type}')
            self.rb_elapsed.setText(f'耗时: {elapsed:.0f}ms')

            if resp.get('success'):
                data = resp.get('data')
                row_count = data.get('row_count', 0) if data else 0
                self.rb_rows.setText(f'行数: {row_count}')
                self.rb_status.setText('✓ 执行成功')
                self.rb_status.setStyleSheet(f'color: {SUCCESS_COLOR}; font-weight: bold;')

                if data and data.get('columns'):
                    self._show_table(data)
                    self._show_log(f'✓ 执行成功 · {row_count} 行 · {elapsed:.0f}ms\n结果已展示在 B 栏数据表格中')
                else:
                    self._show_log(f'✓ 执行成功\n受影响行数: {row_count}\n耗时: {elapsed:.0f}ms')
            else:
                self.rb_rows.setText('行数: —')
                self.rb_status.setText('✗ 执行失败')
                self.rb_status.setStyleSheet(f'color: {DANGER_COLOR}; font-weight: bold;')
                error = resp.get('error', '未知错误')
                self._show_log(f'✗ 执行失败\n{error}\n耗时: {elapsed:.0f}ms')
                self.tabs.setCurrentIndex(0)  # 切到日志 tab 显示错误

            # 保存历史
            history = load_history()
            history.append({
                'sql': sql[:200],
                'success': resp.get('success', False),
                'elapsed': f'{elapsed:.0f}ms',
                'time': datetime.now().strftime('%m/%d %H:%M'),
            })
            save_history(history)
            self._refresh_history()

        self._run_async(do_execute, callback)

    # ── 表格展示 ────────────────────────────
    def _show_table(self, data: Dict):
        """执行SQL结果 → 新建 查询结果 Tab"""
        cols = data['columns']
        rows = data['rows']
        idx = self._add_data_tab('📋 查询结果', cols, rows, sql='')
        self._render_tab_page(idx)

    def _render_tab_page(self, tab_idx: int = -1):
        """渲染指定Tab的当前页"""
        if tab_idx < 0:
            tab_idx = self.data_tabs.currentIndex()
        info = self._tab_data.get(tab_idx)
        if not info or info.get('is_temp'):
            return
        tbl = self._current_table()
        if not tbl:
            return
        tbl.setRowCount(0)
        start = info['page'] * self.PAGE_SIZE
        rows = info['rows']
        page_rows = rows[start:start + self.PAGE_SIZE]
        tbl.setRowCount(len(page_rows))
        for r, row in enumerate(page_rows):
            for c, val in enumerate(row):
                display = '' if val is None else str(val)
                item = QTableWidgetItem(display)
                if val is None:
                    item.setForeground(QColor(MUTED))
                    item.setToolTip('NULL — 双击输入值')
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                tbl.setItem(r, c, item)
        total = len(rows)
        pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page_label.setText(f'第 {info["page"]+1}/{pages} 页 · 共 {total} 行')

    def _prev_page(self):
        info = self._current_tab_info()
        if info['page'] > 0:
            info['page'] -= 1
            self._render_tab_page()

    def _next_page(self):
        info = self._current_tab_info()
        total = len(info.get('rows', []))
        pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if info['page'] < pages - 1:
            info['page'] += 1
            self._render_tab_page()

    # ── 日志 ────────────────────────────────
    def _append_log(self, msg: str):
        self.log_text.append(msg)

    def _show_log(self, msg: str):
        self.log_text.setPlainText(msg)

    # ── 历史记录 ────────────────────────────
    def _refresh_history(self):
        self.history_list.clear()
        history = load_history()
        for h in reversed(history[-50:]):
            status = '✓' if h.get('success') else '✗'
            label = f"{status} {h.get('time','')} | {h.get('elapsed','')} | {h.get('sql','')[:50]}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, h)
            self.history_list.addItem(item)
        self.sb_history.setText(f'历史: {len(history)} 条')

    def _on_history_click(self, item: QListWidgetItem):
        h = item.data(Qt.UserRole)
        if h and h.get('sql'):
            self.sql_text.setPlainText(h['sql'])

    def _clear_history(self):
        reply = QMessageBox.question(self, '确认', '确定清除所有历史记录？')
        if reply == QMessageBox.Yes:
            save_history([])
            self._refresh_history()

    # ── 其他操作 ────────────────────────────
    def _copy_sql(self):
        sql = self.sql_text.toPlainText().strip()
        if sql and not sql.startswith('-- AI'):
            QApplication.clipboard().setText(sql)
            self.status_bar.showMessage('SQL 已复制到剪贴板', 3000)

    def _export_csv(self):
        info = self._current_tab_info()
        rows = info.get('rows', [])
        cols = info.get('columns', [])
        if not rows:
            QMessageBox.warning(self, '提示', '没有可导出的数据')
            return
        path, _ = QFileDialog.getSaveFileName(self, '导出 CSV', '', 'CSV (*.csv)')
        if not path:
            return
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)
        QMessageBox.information(self, '提示', f'已导出到 {path}')

    def _check_health(self):
        def do_check():
            try:
                r = requests.get(f'{API_BASE}/health', timeout=3)
                return r.json()
            except Exception:
                return None

        def callback(resp):
            if resp and resp.get('database'):
                self.sb_db.setText('● MySQL 已连接')
                self.sb_db.setStyleSheet(f'color: {SUCCESS_COLOR};')
            elif resp:
                self.sb_db.setText('● MySQL 断开')
                self.sb_db.setStyleSheet(f'color: {WARNING_COLOR};')
            else:
                self.sb_db.setText('● API 离线')
                self.sb_db.setStyleSheet(f'color: {DANGER_COLOR};')

        self._run_async(do_check, callback)

    # ── 工具 ────────────────────────────────
    def _run_async(self, target, callback):
        worker = ApiWorker(target)
        worker.finished.connect(callback)
        worker.start()
        # 保持引用防止 GC
        if not hasattr(self, '_workers'):
            self._workers = []
        self._workers.append(worker)


# ═══════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════
def main():
    app = QApplication([])
    app.setStyleSheet(DARK_QSS)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
