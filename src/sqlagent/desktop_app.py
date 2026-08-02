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
                                QLineEdit, QMainWindow, QMenu, QMessageBox,
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

        self.db_edit = QLineEdit('sqlagent')
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

        self._rows: List[List[Any]] = []
        self._page = 0
        self.PAGE_SIZE = 100
        self._current_db: Optional[Dict] = None

        self._setup_ui()
        self._load_data()

    # ── UI 构建 ────────────────────────────
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 三栏分栏: 结构树 | 输入+SQL | 结果
        splitter = QSplitter(Qt.Horizontal)
        root_layout.addWidget(splitter)

        sidebar = QWidget()
        center = QWidget()
        right = QWidget()
        splitter.addWidget(sidebar)
        splitter.addWidget(center)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)   # 固定宽度
        splitter.setStretchFactor(1, 42)
        splitter.setStretchFactor(2, 58)
        splitter.setHandleWidth(4)
        sidebar.setFixedWidth(220)

        self._build_sidebar(sidebar)
        self._build_center(center)
        self._build_right(right)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.sb_db = QLabel('● 检测中...')
        self.sb_history = QLabel('')
        self.status_bar.addWidget(self.sb_db)
        self.status_bar.addPermanentWidget(self.sb_history)

    def _build_center(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 4, 4)
        layout.setSpacing(6)

        # ── DB 配置栏 ──
        db_bar = QHBoxLayout()
        self.db_combo = QComboBox()
        self.db_combo.setMinimumHeight(28)
        self.db_combo.currentIndexChanged.connect(self._on_db_select)
        db_bar.addWidget(self.db_combo, 1)

        add_btn = QPushButton('+')
        add_btn.setFixedSize(28, 28)
        add_btn.clicked.connect(self._add_db_dialog)
        db_bar.addWidget(add_btn)

        test_btn = QPushButton('测')
        test_btn.setFixedSize(28, 28)
        test_btn.clicked.connect(self._test_db)
        db_bar.addWidget(test_btn)

        self.db_status = QLabel('')
        self.db_status.setStyleSheet(f'color: {MUTED}; font-size: 11px;')
        db_bar.addWidget(self.db_status)
        layout.addLayout(db_bar)

        # ── 自然语言输入 ──
        nl_group = QGroupBox('自然语言输入')
        nl_ly = QVBoxLayout(nl_group)
        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText(
            '用中文描述你想要查询/修改的数据...\n'
            '例: 查询本月订单总数、统计每个用户消费金额'
        )
        self.input_text.setMaximumHeight(120)
        nl_ly.addWidget(self.input_text)

        btn_row = QHBoxLayout()
        self.gen_btn = QPushButton('生成 SQL')
        self.gen_btn.setProperty('accent', True)
        self.gen_btn.clicked.connect(self._generate_sql)
        btn_row.addWidget(self.gen_btn)

        clear_btn = QPushButton('清空')
        clear_btn.clicked.connect(lambda: self.input_text.clear())
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        nl_ly.addLayout(btn_row)
        layout.addWidget(nl_group)

        # ── SQL 预览 ──
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

        # 高亮器
        self.highlighter = SqlHighlighter(self.sql_text.document())

        # 执行按钮
        exec_row = QHBoxLayout()
        self.exec_btn = QPushButton('执行 SQL')
        self.exec_btn.setProperty('accent', True)
        self.exec_btn.clicked.connect(self._execute_sql)
        exec_row.addWidget(self.exec_btn)

        export_btn = QPushButton('导出 CSV')
        export_btn.clicked.connect(self._export_csv)
        exec_row.addWidget(export_btn)

        self.tx_check = QCheckBox('开启事务')
        exec_row.addWidget(self.tx_check)

        exec_row.addStretch()

        copy_btn = QPushButton('复制 SQL')
        copy_btn.clicked.connect(self._copy_sql)
        exec_row.addWidget(copy_btn)
        sql_ly.addLayout(exec_row)
        layout.addWidget(sql_group, 1)

    def _build_sidebar(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(6, 8, 2, 4)
        layout.setSpacing(6)

        # DB 连接管理
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel('📊 数据库'))
        hdr.addStretch()
        add_conn_btn = QPushButton('+')
        add_conn_btn.setFixedSize(22, 22)
        add_conn_btn.setToolTip('新增数据库连接')
        add_conn_btn.clicked.connect(self._add_db_dialog)
        hdr.addWidget(add_conn_btn)
        refresh_btn = QPushButton('↻')
        refresh_btn.setFixedSize(22, 22)
        refresh_btn.setToolTip('刷新结构')
        refresh_btn.clicked.connect(self._load_schema_tree)
        hdr.addWidget(refresh_btn)
        layout.addLayout(hdr)

        # 结构树 (占满整栏)
        self.schema_tree = QTreeWidget()
        self.schema_tree.setHeaderHidden(True)
        self.schema_tree.setIndentation(14)
        self.schema_tree.setIconSize(QSize(18, 18))
        self.schema_tree.itemExpanded.connect(self._on_tree_expand)
        self.schema_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.schema_tree.customContextMenuRequested.connect(self._on_tree_menu)
        layout.addWidget(self.schema_tree, 1)

        self.tree_label = QLabel('')
        self.tree_label.setStyleSheet(f'color: {MUTED}; font-size: 10px;')
        self.tree_label.setWordWrap(True)
        layout.addWidget(self.tree_label)

        # 连接切换
        conn_row = QHBoxLayout()
        self.sidebar_combo = QComboBox()
        self.sidebar_combo.setMinimumHeight(24)
        self.sidebar_combo.setToolTip('切换数据库连接')
        self.sidebar_combo.currentIndexChanged.connect(self._on_sidebar_db_select)
        conn_row.addWidget(self.sidebar_combo, 1)
        manage_btn = QPushButton('⚙')
        manage_btn.setFixedSize(22, 22)
        manage_btn.setToolTip('管理连接')
        manage_btn.clicked.connect(self._add_db_dialog)
        conn_row.addWidget(manage_btn)
        layout.addLayout(conn_row)

    def _build_right(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(4, 8, 8, 4)
        layout.setSpacing(4)

        # ── 执行状态 ──
        stat_row = QHBoxLayout()
        self.rb_type = QLabel('类型: —')
        self.rb_elapsed = QLabel('耗时: —')
        self.rb_rows = QLabel('行数: —')
        self.rb_status = QLabel('')
        for lbl in [self.rb_type, self.rb_elapsed, self.rb_rows]:
            lbl.setStyleSheet(f'color: {MUTED}; font-size: 12px;')
            stat_row.addWidget(lbl)
        stat_row.addStretch()
        stat_row.addWidget(self.rb_status)
        layout.addLayout(stat_row)

        # ── Tab 容器 ──
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        # Tab 1: 查询结果
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.tabs.addTab(self.result_table, '查询结果')

        # 翻页
        page_widget = QWidget()
        page_layout = QHBoxLayout(page_widget)
        page_layout.setContentsMargins(0, 0, 0, 0)
        self.page_label = QLabel('')
        self.page_label.setStyleSheet(f'color: {MUTED}; font-size: 11px;')
        page_layout.addWidget(self.page_label)
        page_layout.addStretch()
        prev_btn = QPushButton('← 上一页')
        prev_btn.setFixedHeight(24)
        prev_btn.clicked.connect(self._prev_page)
        page_layout.addWidget(prev_btn)
        next_btn = QPushButton('下一页 →')
        next_btn.setFixedHeight(24)
        next_btn.clicked.connect(self._next_page)
        page_layout.addWidget(next_btn)
        layout.addWidget(page_widget)

        # Tab 2: 执行日志
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Consolas', 10))
        self.tabs.addTab(self.log_text, '执行日志')
        self._show_log('在左侧输入问题，点击「生成 SQL」，然后「执行 SQL」\n查询结果将显示在这里')

        # Tab 3: 历史记录
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self._on_history_click)
        self.tabs.addTab(self.history_list, '历史记录')

    # ── 数据加载 ────────────────────────────
    def _load_data(self):
        load_db_configs()
        self._refresh_db_combo()
        self._refresh_history()
        self._check_health()

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

    def _show_table_structure(self, table_name: str, columns: list):
        """在右侧表格显示表结构"""
        self._rows = [[c.get('name', ''), c.get('type', ''), c.get('key', ''),
                       'YES' if c.get('nullable') else 'NO', str(c.get('default', ''))]
                      for c in columns]
        self._page = 0
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(['字段', '类型', '键', '可空', '默认值'])
        self._render_page()
        self.tabs.setCurrentIndex(0)
        self.rb_type.setText(f'类型: STRUCT')
        self.rb_elapsed.setText(f'耗时: —')
        self.rb_rows.setText(f'字段: {len(columns)}')
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
                r = requests.post(f'{API_BASE}/api/query',
                                  json={'question': question}, timeout=120)
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
                self.tabs.setCurrentIndex(1)
            elif sql and sql.strip():
                # 有提取到的 SQL — 放进预览框
                self.sql_text.setPlainText(sql)
                self._append_log(f'[生成SQL] {question}\n{sql}\n')
            else:
                # 没有 SQL — 只显示 AI 分析在日志区，预览框置灰提示
                self.sql_text.setPlainText('-- AI 未生成 SQL 语句，请查看「执行日志」Tab 中的分析')
                self._show_log(f'🤖 AI 分析 (未生成SQL)\n{"─"*50}\n{answer}')
                self.tabs.setCurrentIndex(1)

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
                    self.tabs.setCurrentIndex(0)
                else:
                    self._show_log(f'✓ 执行成功\n受影响行数: {row_count}\n耗时: {elapsed:.0f}ms')
                    self.tabs.setCurrentIndex(1)
            else:
                self.rb_rows.setText('行数: —')
                self.rb_status.setText('✗ 执行失败')
                self.rb_status.setStyleSheet(f'color: {DANGER_COLOR}; font-weight: bold;')
                error = resp.get('error', '未知错误')
                self._show_log(f'✗ 执行失败\n{error}\n耗时: {elapsed:.0f}ms')
                self.tabs.setCurrentIndex(1)

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
        self._rows = data['rows']
        self._page = 0
        columns = data['columns']

        self.result_table.setColumnCount(len(columns))
        self.result_table.setHorizontalHeaderLabels(columns)
        self.result_table.setRowCount(0)
        self._render_page()

    def _render_page(self):
        self.result_table.setRowCount(0)
        start = self._page * self.PAGE_SIZE
        page_rows = self._rows[start:start + self.PAGE_SIZE]
        self.result_table.setRowCount(len(page_rows))
        for r, row in enumerate(page_rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem('NULL' if val is None else str(val))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.result_table.setItem(r, c, item)

        total = len(self._rows)
        pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page_label.setText(f'第 {self._page + 1}/{pages} 页 · 共 {total} 行')

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._render_page()

    def _next_page(self):
        total = len(self._rows)
        pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self._page < pages - 1:
            self._page += 1
            self._render_page()

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
        if not self._rows:
            QMessageBox.warning(self, '提示', '没有可导出的数据')
            return
        path, _ = QFileDialog.getSaveFileName(self, '导出 CSV', '', 'CSV (*.csv)')
        if not path:
            return
        cols = [self.result_table.horizontalHeaderItem(c).text()
                for c in range(self.result_table.columnCount())]
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(self._rows)
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
