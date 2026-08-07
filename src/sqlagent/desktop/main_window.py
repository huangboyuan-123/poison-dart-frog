"""
主窗口: MainWindow class
"""
from typing import Dict, Optional

import requests
from PySide6 import QtCore
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu,
    QMenuBar, QPushButton, QSplitter, QStackedWidget, QVBoxLayout, QWidget,
)

from .constants import (
    API_BASE, BG, ACCENT_COLOR, MUTED, ICONS_DIR,
)
from .dialogs.table_designer import _RoundedWidget
from .store import load_db_configs
from .panels.panel_a import PanelAMixin
from .panels.panel_b import PanelBMixin
from .panels.panel_c import PanelCMixin
from .redis_panels import RedisPanelsMixin


class MainWindow(QMainWindow, PanelAMixin, PanelBMixin, PanelCMixin, RedisPanelsMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('箭毒蛙')
        self.resize(1200, 780)
        self.setMinimumSize(900, 600)

        self.PAGE_SIZE = 100
        self._current_db: Optional[Dict] = None
        self._c_collapsed = False
        self._c_saved_width = 0

        # 无边框窗口 + 圆角 + 拖拽跟踪
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self._setup_ui()
        self._load_data()

    def _edge_test(self, pos):
        """检测鼠标是否在窗口边缘 (4px 精确线检测)"""
        r = self.rect()
        m = 4
        l = 0 <= pos.x() < m
        ri = r.width() - m < pos.x() <= r.width()
        t = 0 <= pos.y() < m
        b = r.height() - m < pos.y() <= r.height()
        if t and l: return Qt.TopLeftCorner
        if t and ri: return Qt.TopRightCorner
        if b and l: return Qt.BottomLeftCorner
        if b and ri: return Qt.BottomRightCorner
        if t: return Qt.TopEdge
        if b: return Qt.BottomEdge
        if l: return Qt.LeftEdge
        if ri: return Qt.RightEdge
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge = self._edge_test(event.position().toPoint())
            if edge and self.windowHandle():
                self.windowHandle().startSystemResize(edge)
                return
            if event.position().y() < 34:
                self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    # ── UI 构建 ────────────────────────────
    def _setup_ui(self):
        # ── 自定义标题栏 ──
        titlebar = QWidget()
        titlebar.setFixedHeight(34)
        titlebar.setStyleSheet(f'background: #2B2B2B; border-bottom: 1px solid rgba(255,255,255,0.06);')
        tb_layout = QHBoxLayout(titlebar)
        tb_layout.setContentsMargins(10, 0, 0, 0)
        tb_layout.setSpacing(0)

        logo = QLabel('箭毒蛙')
        logo.setStyleSheet('color: #86909C; font-size: 12px; font-weight: 600; background: transparent; border: none;')
        tb_layout.addWidget(logo)
        tb_layout.addStretch()

        ctrl_style = 'QPushButton { background: transparent; border: none; color: #86909C; font-size: 14px; padding: 0 12px; } QPushButton:hover { background: rgba(255,255,255,0.06); } QPushButton#btnClose:hover { background: #E05555; color: white; }'
        min_btn = QPushButton('─')
        min_btn.setObjectName('btnMin')
        min_btn.setStyleSheet(ctrl_style)
        min_btn.clicked.connect(self.showMinimized)
        tb_layout.addWidget(min_btn)

        max_btn = QPushButton('□')
        max_btn.setStyleSheet(ctrl_style)
        max_btn.clicked.connect(lambda: self.showMaximized() if not self.isMaximized() else self.showNormal())
        tb_layout.addWidget(max_btn)

        close_btn = QPushButton('✕')
        close_btn.setObjectName('btnClose')
        close_btn.setStyleSheet(ctrl_style)
        close_btn.clicked.connect(self.close)
        tb_layout.addWidget(close_btn)

        # ── 菜单栏 ──
        menubar = QMenuBar()
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

        set_menu = menubar.addMenu('设置')
        act_ai = QAction('AI 配置', self)
        act_ai.triggered.connect(self._open_settings)
        set_menu.addAction(act_ai)

        switch_menu = menubar.addMenu('切换')
        home_icon = QIcon(str(ICONS_DIR / 'home.png'))
        act_home = QAction(home_icon, '首页', self)
        act_home.triggered.connect(lambda: self._switch_workspace('home'))
        switch_menu.addAction(act_home)
        act_mysql = QAction('\U0001f41f MySQL', self)  # fish emoji (dolphin)
        act_mysql.triggered.connect(lambda: self._switch_workspace('mysql'))
        switch_menu.addAction(act_mysql)
        act_redis = QAction('\U0001f534 Redis', self)  # red circle
        act_redis.triggered.connect(lambda: self._switch_workspace('redis'))
        switch_menu.addAction(act_redis)

        tools_menu = menubar.addMenu('工具')
        act_export = QAction('导出数据 (CSV/Excel)', self)
        act_export.triggered.connect(self._export_csv)
        tools_menu.addAction(act_export)
        act_import = QAction('导入数据 (CSV/Excel/JSON)', self)
        act_import.triggered.connect(self._import_data)
        tools_menu.addAction(act_import)
        tools_menu.addSeparator()
        act_clear_hist = QAction('清除历史记录', self)
        act_clear_hist.triggered.connect(self._clear_history)
        tools_menu.addAction(act_clear_hist)

        central = _RoundedWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(3, 3, 3, 3)
        root_layout.setSpacing(0)

        root_layout.addWidget(titlebar)
        root_layout.addWidget(menubar)

        # QStackedWidget: Page0=首页, Page1=MySQL, Page2=Redis
        self.stack = QStackedWidget()

        # ── Page 0: 首页 ──
        home = QWidget()
        home_layout = QVBoxLayout(home)
        home_layout.setAlignment(Qt.AlignCenter)
        home_layout.setSpacing(20)

        title = QLabel('箭毒蛙')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('font-size: 28px; font-weight: bold; color: #4A88C7;')
        home_layout.addWidget(title)

        subtitle = QLabel('选择数据源类型开始')
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f'font-size: 14px; color: {MUTED}; margin-bottom: 20px;')
        home_layout.addWidget(subtitle)

        cards = QHBoxLayout()
        cards.setAlignment(Qt.AlignCenter)
        cards.setSpacing(30)

        # MySQL 卡片
        mysql_card = QFrame()
        mysql_card.setFixedSize(200, 260)
        mysql_card.setCursor(Qt.CursorShape.PointingHandCursor)
        mysql_card.setStyleSheet(f"""
            QFrame {{ background: {BG}; border: 2px solid rgba(37,116,255,0.2); border-radius: 12px; }}
            QFrame:hover {{ border-color: #00BFA5; background: #3C3F41; }}
        """)
        mysql_card.mousePressEvent = lambda e: self._switch_workspace('mysql')
        ml = QVBoxLayout(mysql_card)
        ml.setAlignment(Qt.AlignCenter)
        ml.setSpacing(8)
        mi = QLabel('\U0001f41f'); mi.setAlignment(Qt.AlignCenter); mi.setStyleSheet('font-size: 56px; border:none;')
        ml.addWidget(mi)
        mt = QLabel('MySQL'); mt.setAlignment(Qt.AlignCenter)
        mt.setStyleSheet('font-size: 20px; font-weight: bold; color: #A9B7C6; border:none;')
        ml.addWidget(mt)
        md = QLabel('关系型数据库\n表结构 · SQL查询 · 数据编辑'); md.setAlignment(Qt.AlignCenter)
        md.setStyleSheet(f'font-size: 12px; color: {MUTED}; border:none;')
        ml.addWidget(md)
        cards.addWidget(redis_card)

        # MySQL 卡片(附属)
        redis_card = QFrame()
        redis_card.setFixedSize(250, 300)
        redis_card.setCursor(Qt.CursorShape.PointingHandCursor)
        redis_card.setStyleSheet(f"""
            QFrame {{ background: {BG}; border: 2px solid rgba(0,191,165,0.3); border-radius: 12px; }}
            QFrame:hover {{ border-color: #00BFA5; background: #3C3F41; }}
        """)
        redis_card.mousePressEvent = lambda e: self._switch_workspace('redis')
        rl = QVBoxLayout(redis_card)
        rl.setAlignment(Qt.AlignCenter)
        rl.setSpacing(8)
        ri = QLabel('\U0001f534'); ri.setAlignment(Qt.AlignCenter); ri.setStyleSheet('font-size: 56px; border:none;')
        rl.addWidget(ri)
        rt = QLabel('Redis'); rt.setAlignment(Qt.AlignCenter)
        rt.setStyleSheet('font-size: 20px; font-weight: bold; color: #A9B7C6; border:none;')
        rl.addWidget(rt)
        rd = QLabel('键值数据库\n键浏览 · 值查看 · 缓存管理'); rd.setAlignment(Qt.AlignCenter)
        rd.setStyleSheet(f'font-size: 12px; color: {MUTED}; border:none;')
        rl.addWidget(rd)
        cards.addWidget(mysql_card)

        home_layout.addLayout(cards)

        self.stack.addWidget(home)  # index 0

        # ── Page 1: MySQL workspace ──
        mysql_ws = QWidget()
        mysql_ws_layout = QVBoxLayout(mysql_ws)
        mysql_ws_layout.setContentsMargins(0, 0, 0, 0)
        mysql_ws_layout.setSpacing(0)

        # panel_c and panel_d (built here, added to top splitter later)
        panel_c = QWidget()
        panel_d = QWidget()
        self.panel_c = panel_c
        self.panel_d = panel_d
        self._build_panel_c(panel_c)
        self._build_panel_d(panel_d)
        panel_d.hide()

        mysql_splitter = QSplitter(Qt.Horizontal)
        panel_a = QWidget()
        panel_b = QWidget()
        mysql_splitter.addWidget(panel_a)
        mysql_splitter.addWidget(panel_b)
        mysql_splitter.setStretchFactor(0, 0)
        mysql_splitter.setStretchFactor(1, 1)
        mysql_splitter.setHandleWidth(4)
        panel_a.setFixedWidth(200)
        self._build_panel_a(panel_a)
        self._build_panel_b(panel_b)
        mysql_ws_layout.addWidget(mysql_splitter, 1)
        self.stack.addWidget(mysql_ws)  # index 1

        # ── Page 2: Redis workspace ──
        redis_ws = QWidget()
        redis_ws_layout = QVBoxLayout(redis_ws)
        redis_ws_layout.setContentsMargins(0, 0, 0, 0)
        redis_ws_layout.setSpacing(0)
        redis_splitter = QSplitter(Qt.Horizontal)
        ra = QWidget()
        rb = QWidget()
        redis_splitter.addWidget(ra)
        redis_splitter.addWidget(rb)
        redis_splitter.setStretchFactor(0, 0)
        redis_splitter.setStretchFactor(1, 1)
        redis_splitter.setHandleWidth(4)
        ra.setFixedWidth(250)
        self._build_redis_panel_a(ra)
        self._build_redis_panel_b(rb)
        redis_ws_layout.addWidget(redis_splitter, 1)
        self.stack.addWidget(redis_ws)  # index 2

        # 顶层: stack(左) + C+D(右)
        top_splitter = QSplitter(Qt.Horizontal)
        top_splitter.addWidget(self.stack)
        top_splitter.addWidget(panel_c)
        top_splitter.addWidget(panel_d)
        top_splitter.setStretchFactor(0, 1)
        top_splitter.setStretchFactor(1, 0)
        top_splitter.setStretchFactor(2, 0)
        top_splitter.setHandleWidth(4)
        self._splitter = top_splitter
        root_layout.addWidget(top_splitter)

        self.stack.setCurrentIndex(0)

    def _switch_workspace(self, mode: str):
        """切换工作区: home / mysql / redis"""
        self._current_workspace = mode
        if mode == 'home':
            self.stack.setCurrentIndex(0)
        elif mode == 'mysql':
            self.stack.setCurrentIndex(1)
            if not hasattr(self, '_mysql_loaded'):
                self._load_data()
                self._mysql_loaded = True
        elif mode == 'redis':
            self.stack.setCurrentIndex(2)
            if not hasattr(self, '_redis_loaded'):
                self._load_redis_keys()
                self._redis_loaded = True

    # ── 数据加载 ────────────────────────────
    def _load_data(self):
        load_db_configs()
        self._refresh_db_combo()
        self._refresh_history()
        self._load_schema_tree()
