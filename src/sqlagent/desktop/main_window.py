"""
箭毒蛙 Redis 专用版 — 主窗口
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QAction, QColor, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame,
                                QGroupBox, QHBoxLayout, QInputDialog, QLabel,
                                QLineEdit, QMainWindow, QMenu, QMenuBar,
                                QMessageBox, QPlainTextEdit, QPushButton,
                                QSplitter, QStackedWidget, QTableWidget,
                                QTableWidgetItem, QTextEdit, QTreeWidget,
                                QTreeWidgetItem, QVBoxLayout, QWidget)

from . import constants as C
from .redis_dialogs import (RedisConnDialog, NewKeyDialog, TTLDialog,
                             _redis_configs, load_redis_configs, save_redis_configs)
from .workers import StreamWorker, ApiWorker
from .utils import _md_to_html, _extract_redis_commands


class _RoundedWidget(QFrame):
    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QPainterPath, QBrush
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath(); path.addRoundedRect(self.rect(), 10, 10)
        p.fillPath(path, QBrush(QColor(C.BG)))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('箭毒蛙 — Redis AI 管理工具')
        self.resize(1200, 780); self.setMinimumSize(900, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._drag_pos = None
        self._current_conn: Optional[Dict] = None
        self._current_key = ''
        self._think_buffer = ''
        self._setup_ui()
        load_redis_configs()
        if _redis_configs:
            self._current_conn = _redis_configs[0]
        self._refresh_conn_combo()
        self._load_redis_keys()

    def _edge_test(self, pos):
        r, m = self.rect(), 4
        l = 0 <= pos.x() < m; ri = r.width() - m < pos.x() <= r.width()
        t = 0 <= pos.y() < m; b = r.height() - m < pos.y() <= r.height()
        if t and l: return Qt.TopLeftCorner
        if t and ri: return Qt.TopRightCorner
        if b and l: return Qt.BottomLeftCorner
        if b and ri: return Qt.BottomRightCorner
        if t: return Qt.TopEdge
        if b: return Qt.BottomEdge
        if l: return Qt.LeftEdge
        if ri: return Qt.RightEdge

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge = self._edge_test(event.position().toPoint())
            if edge and self.windowHandle():
                self.windowHandle().startSystemResize(edge); return
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
        self._drag_pos = None; super().mouseReleaseEvent(event)

    def _setup_ui(self):
        tb = QWidget(); tb.setFixedHeight(34)
        tb.setStyleSheet(f'background: {C.BG}; border-bottom: 1px solid rgba(255,255,255,0.06);')
        tl = QHBoxLayout(tb); tl.setContentsMargins(10, 0, 0, 0)
        logo = QLabel('箭毒蛙 — Redis AI')
        logo.setStyleSheet(f'color: {C.MUTED}; font-size: 12px; font-weight: 600; background: transparent;')
        tl.addWidget(logo); tl.addStretch()
        css = 'QPushButton{background:transparent;border:none;color:#86909C;font-size:14px;padding:0 12px;}QPushButton:hover{background:rgba(255,255,255,0.06);}'
        for sym, fn in [('─', self.showMinimized), ('□', lambda: self.showMaximized() if not self.isMaximized() else self.showNormal()), ('✕', self.close)]:
            b = QPushButton(sym); b.setStyleSheet(css); b.clicked.connect(fn); tl.addWidget(b)

        mb = QMenuBar()
        mb.setStyleSheet(f"QMenuBar{{background:{C.BG};color:{C.MUTED};border-bottom:1px solid rgba(255,255,255,0.06);padding:2px 0;}}QMenuBar::item{{padding:4px 12px;}}QMenuBar::item:selected{{background:{C.ACCENT_COLOR};color:white;}}")
        fm = mb.addMenu('文件')
        fm.addAction('新增连接', self._add_conn_dialog)
        fm.addAction('导入JSON', self._import_json)
        fm.addAction('导出JSON', self._export_json)
        fm.addSeparator(); fm.addAction('退出', self.close)
        tm = mb.addMenu('工具')
        tm.addAction('新建键', self._new_key_dialog)
        tm.addAction('清空数据库', self._flush_db)
        sm = mb.addMenu('切换')
        sm.addAction(QIcon(str(C.ICONS_DIR / 'home.png')), '首页', lambda: self._switch_page('home'))
        sm.addAction('🔴 Redis', lambda: self._switch_page('redis'))

        central = _RoundedWidget(self); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(3, 3, 3, 3); root.setSpacing(0)
        root.addWidget(tb); root.addWidget(mb)

        self.stack = QStackedWidget()
        self._build_home(); self._build_redis_ws()
        root.addWidget(self.stack)

    def _build_home(self):
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignCenter); l.setSpacing(16)
        t = QLabel('箭毒蛙 — Redis AI 管理工具'); t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet(f'font-size: 26px; font-weight: bold; color: {C.ACCENT_COLOR};'); l.addWidget(t)
        card = QFrame(); card.setFixedSize(220, 260)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"QFrame{{background:{C.BG};border:2px solid rgba(220,50,50,0.2);border-radius:12px;}}QFrame:hover{{border-color:#DC3232;background:#3C3F41;}}")
        card.mousePressEvent = lambda e: self._switch_page('redis')
        cl = QVBoxLayout(card); cl.setAlignment(Qt.AlignCenter); cl.setSpacing(8)
        ci = QLabel('🔴'); ci.setAlignment(Qt.AlignCenter); ci.setStyleSheet('font-size:56px;border:none;'); cl.addWidget(ci)
        ct = QLabel('Redis'); ct.setAlignment(Qt.AlignCenter); ct.setStyleSheet('font-size:20px;font-weight:bold;color:#A9B7C6;border:none;'); cl.addWidget(ct)
        cd = QLabel('键值数据库\nAI 智能管理 · 全类型编辑 · 监控'); cd.setAlignment(Qt.AlignCenter)
        cd.setStyleSheet(f'font-size:12px;color:{C.MUTED};border:none;'); cl.addWidget(cd)
        cr = QHBoxLayout(); cr.setAlignment(Qt.AlignCenter); cr.addWidget(card); l.addLayout(cr)
        self.stack.addWidget(w)

    def _build_redis_ws(self):
        ws = QWidget(); wl = QVBoxLayout(ws); wl.setContentsMargins(0, 0, 0, 0); wl.setSpacing(0)
        top = QSplitter(Qt.Horizontal)
        ab = QSplitter(Qt.Horizontal)
        ra = QWidget(); rb = QWidget()
        self.panel_d = QWidget()
        ab.addWidget(ra); ab.addWidget(rb)
        ab.setStretchFactor(0, 0); ab.setStretchFactor(1, 1); ab.setHandleWidth(4); ra.setFixedWidth(260)
        self._build_a(ra); self._build_b(rb)
        top.addWidget(ab)
        pc = QWidget(); self._build_c(pc); top.addWidget(pc)
        self._build_d(self.panel_d); top.addWidget(self.panel_d)
        top.setStretchFactor(0, 1); top.setStretchFactor(1, 0); top.setStretchFactor(2, 0); top.setHandleWidth(4)
        self.panel_d.hide(); self._splitter = top
        wl.addWidget(top, 1); self.stack.addWidget(ws)

    def _switch_page(self, mode):
        self.stack.setCurrentIndex(0 if mode == 'home' else 1)

    # ═══ A: 键浏览 ═══
    def _build_a(self, p):
        l = QVBoxLayout(p); l.setContentsMargins(4, 8, 2, 4); l.setSpacing(4)
        cr = QHBoxLayout()
        self.conn_combo = QComboBox(); self.conn_combo.setMinimumHeight(24)
        self.conn_combo.currentIndexChanged.connect(self._on_conn_select); cr.addWidget(self.conn_combo, 1)
        for t, f in [('+', self._add_conn_dialog), ('✕', self._del_conn)]:
            b = QPushButton(t); b.setFixedSize(22, 22); b.clicked.connect(f); cr.addWidget(b)
        l.addLayout(cr)
        sr = QHBoxLayout()
        self.key_filter = QLineEdit(); self.key_filter.setPlaceholderText('键模式 (* 查全部)')
        self.key_filter.returnPressed.connect(self._load_redis_keys); sr.addWidget(self.key_filter)
        for t, f in [('刷新', self._load_redis_keys), ('+键', self._new_key_dialog)]:
            b = QPushButton(t); b.setFixedHeight(22); b.clicked.connect(f); sr.addWidget(b)
        l.addLayout(sr)
        self.redis_tree = QTreeWidget(); self.redis_tree.setHeaderHidden(True); self.redis_tree.setIndentation(12)
        self.redis_tree.itemClicked.connect(self._on_key_click)
        self.redis_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.redis_tree.customContextMenuRequested.connect(self._on_key_menu)
        l.addWidget(self.redis_tree, 1)

    def _refresh_conn_combo(self):
        self.conn_combo.clear()
        for c in _redis_configs:
            self.conn_combo.addItem(f"{c['name']} ({c['host']}:{c['port']})", c)

    def _on_conn_select(self, idx):
        if 0 <= idx < len(_redis_configs):
            self._current_conn = _redis_configs[idx]; self._load_redis_keys()

    def _add_conn_dialog(self):
        dlg = RedisConnDialog(self)
        if dlg.exec():
            cfg = dlg.get_config(); _redis_configs.append(cfg); save_redis_configs()
            self._refresh_conn_combo(); self._current_conn = cfg; self._load_redis_keys()

    def _del_conn(self):
        idx = self.conn_combo.currentIndex()
        if idx >= 0 and QMessageBox.question(self, '确认', '删除当前连接?') == QMessageBox.Yes:
            del _redis_configs[idx]; save_redis_configs(); self._refresh_conn_combo()

    def _load_redis_keys(self):
        pattern = self.key_filter.text() or '*'; self.redis_tree.clear()
        def do():
            return requests.get(f'{C.API_BASE}/api/redis/keys?pattern={pattern}', timeout=5).json()
        def cb(data):
            tree_map = {}
            for key in sorted(data.get('keys', [])):
                parts = key.split(':')
                for i, part in enumerate(parts):
                    fp = ':'.join(parts[:i+1])
                    if i == len(parts) - 1:
                        item = QTreeWidgetItem([part])
                        item.setData(0, Qt.UserRole + 1, 'key'); item.setToolTip(0, str(key))
                        tc = data.get('types', {}).get(key, '')
                        if tc: item.setForeground(0, QColor(tc))
                        pp = ':'.join(parts[:i]) if i > 0 else ''
                        (tree_map[pp].addChild(item) if pp in tree_map else self.redis_tree.addTopLevelItem(item))
                    elif fp not in tree_map:
                        item = QTreeWidgetItem([part])
                        pp = ':'.join(parts[:i]) if i > 0 else ''
                        (tree_map[pp].addChild(item) if pp in tree_map else self.redis_tree.addTopLevelItem(item))
                        tree_map[fp] = item
        self._run_async(do, cb)

    def _on_key_click(self, item, _):
        if item.data(0, Qt.UserRole + 1) != 'key': return
        self._current_key = item.toolTip(0); self._show_key(self._current_key)

    def _show_key(self, key):
        self.k_label.setText(f'键: {key}')
        def do(): return requests.get(f'{C.API_BASE}/api/redis/key/{key}', timeout=5).json()
        def cb(d):
            self.t_label.setText(f'类型: {d.get("type","")}')
            try:
                tt = requests.get(f'{C.API_BASE}/api/redis/ttl/{key}', timeout=3).json().get('ttl', -1)
                self.ttl_lbl.setText(f'TTL: {tt}s' if tt > 0 else 'TTL: 永久')
            except: pass
            v, t = d.get('value', ''), d.get('type', 'string')
            if t == 'hash': self._show_hash(v if isinstance(v, dict) else {})
            elif t == 'list': self._show_list(v if isinstance(v, list) else [])
            elif t == 'set': self._show_set(v if isinstance(v, list) else [])
            elif t == 'zset': self._show_zset(v if isinstance(v, list) else [])
            else:
                self.vs.setCurrentIndex(0); self.str_edit.setPlainText(str(v) if v else '')
        self._run_async(do, cb)

    # ═══ B: 值查看器 ═══
    def _build_b(self, p):
        l = QVBoxLayout(p); l.setContentsMargins(4, 8, 8, 4); l.setSpacing(4)
        ir = QHBoxLayout()
        self.k_label = QLabel('选择一个键'); self.k_label.setStyleSheet('font-weight:bold;font-size:13px;')
        ir.addWidget(self.k_label); ir.addStretch()
        self.t_label = QLabel(''); ir.addWidget(self.t_label)
        self.ttl_lbl = QLabel(''); self.ttl_lbl.setStyleSheet(f'color:{C.MUTED};'); ir.addWidget(self.ttl_lbl)
        l.addLayout(ir)

        self.vs = QStackedWidget()
        w0 = QWidget(); w0l = QVBoxLayout(w0); w0l.setContentsMargins(0,0,0,0)
        self.str_edit = QTextEdit(); self.str_edit.setFont(QFont('Consolas', 10)); w0l.addWidget(self.str_edit)
        self.vs.addWidget(w0)
        for cols in [['Field', 'Value'], ['元素'], ['成员'], ['成员', '分数']]:
            t = QTableWidget(0, len(cols)); t.setHorizontalHeaderLabels(cols)
            t.horizontalHeader().setStretchLastSection(True); self.vs.addWidget(t)
        l.addWidget(self.vs, 1)

        br = QHBoxLayout()
        self.save_btn = QPushButton(QIcon(str(C.ICONS_DIR / 'diskette.png')), '保存')
        self.save_btn.setProperty('accent', True); self.save_btn.clicked.connect(self._save_val); br.addWidget(self.save_btn)
        for t, f in [('🗑 删除', self._del_key), ('⏱ TTL', self._set_ttl), ('✏ 重命名', self._rename_key)]:
            b = QPushButton(t); b.clicked.connect(f); br.addWidget(b)
        br.addStretch(); l.addLayout(br)

    def _show_hash(self, d): self.vs.setCurrentIndex(1); t = self.vs.widget(1); t.setRowCount(len(d)); [t.setItem(r, 0, QTableWidgetItem(k)) or t.setItem(r, 1, QTableWidgetItem(str(v))) for r, (k, v) in enumerate(d.items())]
    def _show_list(self, d): self.vs.setCurrentIndex(2); t = self.vs.widget(2); t.setRowCount(len(d)); [t.setItem(r, 0, QTableWidgetItem(str(v))) for r, v in enumerate(d)]
    def _show_set(self, d): self.vs.setCurrentIndex(3); t = self.vs.widget(3); t.setRowCount(len(d)); [t.setItem(r, 0, QTableWidgetItem(str(v))) for r, v in enumerate(d)]
    def _show_zset(self, d): self.vs.setCurrentIndex(4); t = self.vs.widget(4); t.setRowCount(len(d)); [t.setItem(r, 0, QTableWidgetItem(str(v[0]))) or t.setItem(r, 1, QTableWidgetItem(str(v[1]))) for r, v in enumerate(d) if isinstance(v, (tuple, list))]

    def _save_val(self):
        k, idx = self._current_key, self.vs.currentIndex()
        if not k: return
        try:
            if idx == 0:
                requests.post(f'{C.API_BASE}/api/redis/key/{k}', json={'value': self.str_edit.toPlainText()})
            elif idx == 1:
                t = self.vs.widget(1)
                vals = {t.item(r, 0).text(): (t.item(r, 1).text() if t.item(r, 1) else '') for r in range(t.rowCount()) if t.item(r, 0)}
                requests.post(f'{C.API_BASE}/api/redis/hash/{k}', json={'values': vals})
            elif idx == 2:
                t = self.vs.widget(2)
                items = [t.item(r, 0).text() for r in range(t.rowCount()) if t.item(r, 0)]
                requests.post(f'{C.API_BASE}/api/redis/list/{k}', json={'items': items})
            elif idx == 3:
                t = self.vs.widget(3)
                mems = [t.item(r, 0).text() for r in range(t.rowCount()) if t.item(r, 0)]
                requests.post(f'{C.API_BASE}/api/redis/set/{k}', json={'members': mems})
            elif idx == 4:
                t = self.vs.widget(4); entries = {}
                for r in range(t.rowCount()):
                    m = t.item(r, 0).text() if t.item(r, 0) else ''; s = t.item(r, 1).text() if t.item(r, 1) else '0'
                    if m: entries[m] = float(s)
                requests.post(f'{C.API_BASE}/api/redis/zset/{k}', json={'entries': entries})
            self._load_redis_keys()
        except Exception as e:
            QMessageBox.warning(self, '错误', str(e))

    def _del_key(self):
        if not self._current_key: return
        if QMessageBox.question(self, '确认', f'删除 {self._current_key}?') == QMessageBox.Yes:
            requests.delete(f'{C.API_BASE}/api/redis/key/{self._current_key}'); self._load_redis_keys()

    def _set_ttl(self):
        if not self._current_key: return
        try: cur = requests.get(f'{C.API_BASE}/api/redis/ttl/{self._current_key}', timeout=3).json().get('ttl', -1)
        except: cur = -1
        dlg = TTLDialog(self._current_key, cur, self)
        if dlg.exec():
            t = dlg.get_ttl()
            if t < 0: requests.post(f'{C.API_BASE}/api/redis/persist/{self._current_key}')
            else: requests.post(f'{C.API_BASE}/api/redis/expire/{self._current_key}', json={'ttl': t})
            self._show_key(self._current_key)

    def _rename_key(self):
        if not self._current_key: return
        n, ok = QInputDialog.getText(self, '重命名', '新键名:', text=self._current_key)
        if ok and n:
            r = requests.post(f'{C.API_BASE}/api/redis/rename/{self._current_key}', json={'new_name': n}).json()
            if r.get('ok'): self._load_redis_keys()

    def _on_key_menu(self, pos):
        item = self.redis_tree.itemAt(pos)
        if not item or item.data(0, Qt.UserRole + 1) != 'key': return
        k = item.toolTip(0); self._current_key = k
        m = QMenu(self)
        m.addAction('查看值', lambda: self._show_key(k))
        m.addAction('设置TTL', self._set_ttl)
        m.addAction('重命名', self._rename_key)
        m.addSeparator()
        m.addAction('🗑 删除', self._del_key)
        m.addAction('复制键名', lambda: QApplication.clipboard().setText(k))
        m.exec(self.redis_tree.mapToGlobal(pos))

    def _new_key_dialog(self):
        dlg = NewKeyDialog(self)
        if dlg.exec():
            k, t, v = dlg.get_data()
            if k:
                requests.post(f'{C.API_BASE}/api/redis/new', json={'key': k, 'type': t, 'value': v}); self._load_redis_keys()

    def _export_json(self):
        p, _ = QFileDialog.getSaveFileName(self, '导出', '', 'JSON (*.json)')
        if p:
            try:
                data = {}
                for i in range(self.redis_tree.topLevelItemCount()):
                    item = self.redis_tree.topLevelItem(i)
                    for j in range(item.childCount()):
                        child = item.child(j)
                        if child.data(0, Qt.UserRole + 1) == 'key':
                            k = child.toolTip(0)
                            data[k] = requests.get(f'{C.API_BASE}/api/redis/key/{k}').json()
                Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2), 'utf-8')
            except Exception as e:
                QMessageBox.warning(self, '错误', str(e))

    def _import_json(self):
        p, _ = QFileDialog.getOpenFileName(self, '导入', '', 'JSON (*.json)')
        if p:
            try:
                data = json.loads(Path(p).read_text('utf-8'))
                for k, v in data.items():
                    requests.post(f'{C.API_BASE}/api/redis/import', json={'key': k, **v})
                self._load_redis_keys()
            except Exception as e:
                QMessageBox.warning(self, '错误', str(e))

    def _flush_db(self):
        if QMessageBox.warning(self, '⚠️ 危险', '清空当前数据库? 不可逆!', QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            requests.post(f'{C.API_BASE}/api/redis/execute', json={'command': 'FLUSHDB'}); self._load_redis_keys()

    # ═══ C: AI ═══
    def _build_c(self, p):
        l = QVBoxLayout(p); l.setContentsMargins(4, 4, 8, 4); l.setSpacing(6)
        tr = QHBoxLayout(); tr.addStretch()
        self.d_toggle = QPushButton('💭 思考'); self.d_toggle.setFixedHeight(20)
        self.d_toggle.clicked.connect(self._toggle_d); tr.addWidget(self.d_toggle); l.addLayout(tr)
        g = QGroupBox('Redis AI'); gl = QVBoxLayout(g)
        self.ai_in = QPlainTextEdit(); self.ai_in.setPlaceholderText('用中文描述 Redis 操作...')
        self.ai_in.setMaximumHeight(80); gl.addWidget(self.ai_in)
        br = QHBoxLayout()
        self.gen_btn = QPushButton('生成命令'); self.gen_btn.setProperty('accent', True)
        self.gen_btn.clicked.connect(self._ai_gen); br.addWidget(self.gen_btn)
        br.addWidget(QPushButton('清空', clicked=lambda: self.ai_in.clear())); br.addStretch(); gl.addLayout(br); l.addWidget(g)
        g2 = QGroupBox('命令预览'); g2l = QVBoxLayout(g2)
        self.cmd_pv = QTextEdit(); self.cmd_pv.setReadOnly(True); self.cmd_pv.setFont(QFont('Consolas', 10))
        g2l.addWidget(self.cmd_pv)
        er = QHBoxLayout()
        self.exec_btn = QPushButton('执行命令'); self.exec_btn.setProperty('accent', True)
        self.exec_btn.clicked.connect(self._ai_exec); er.addWidget(self.exec_btn); er.addStretch(); g2l.addLayout(er)
        l.addWidget(g2, 1)
        self._log = QTextEdit(); self._log.setReadOnly(True); self._log.setMaximumHeight(120); self._log.setFont(QFont('Consolas', 10))
        l.addWidget(self._log)

    # ═══ D: 思考 ═══
    def _build_d(self, p):
        l = QVBoxLayout(p); l.setContentsMargins(4, 8, 8, 4); l.setSpacing(4)
        hr = QHBoxLayout(); hr.addWidget(QLabel('💭 思考过程')); hr.addStretch()
        cb = QPushButton('✕'); cb.setFixedSize(20, 20); cb.setFlat(True)
        cb.setStyleSheet('QPushButton{background:transparent;border:none;color:#86909C;}QPushButton:hover{color:#E05555;}')
        cb.clicked.connect(self._toggle_d); hr.addWidget(cb); l.addLayout(hr)
        self._think = QTextEdit(); self._think.setReadOnly(True); self._think.setFont(QFont('Consolas', 10))
        l.addWidget(self._think, 1)

    def _toggle_d(self):
        if self.panel_d.isVisible():
            self.panel_d.hide(); self._splitter.setStretchFactor(2, 0)
        else:
            self.panel_d.show(); self._splitter.setStretchFactor(2, 25); self._splitter.setStretchFactor(1, 30)

    def _ai_gen(self):
        q = self.ai_in.toPlainText().strip()
        if not q: return
        self.gen_btn.setText('生成中...'); self.gen_btn.setEnabled(False); self._think_buffer = ''
        sw = StreamWorker(f'{C.API_BASE}/api/redis/query/stream', {'question': q})
        full = []
        def on_chunk(ch): full.append(ch); self._think.setHtml(_md_to_html(''.join(full)))
        sw.chunk.connect(on_chunk)
        def on_done(resp):
            self.gen_btn.setText('生成命令'); self.gen_btn.setEnabled(True)
            txt = resp.get('full_text', '')
            if resp.get('error'): self.cmd_pv.setPlainText(f'# 错误: {resp["error"]}'); return
            cmds = _extract_redis_commands(txt)
            self.cmd_pv.setPlainText('\n'.join(cmds) if cmds else txt)
        sw.finished.connect(on_done); sw.start()

    def _ai_exec(self):
        cmd = self.cmd_pv.toPlainText().strip()
        if not cmd: return
        self.exec_btn.setText('执行中...'); self.exec_btn.setEnabled(False)
        try:
            r = requests.post(f'{C.API_BASE}/api/redis/execute', json={'command': cmd}, timeout=10).json()
            self._log.append(f'✓ {r.get("result", "OK")}\n'); self._load_redis_keys()
        except Exception as e:
            self._log.append(f'✗ {e}\n')
        finally:
            self.exec_btn.setText('执行命令'); self.exec_btn.setEnabled(True)

    def _run_async(self, target, callback):
        w = ApiWorker(target); w.finished.connect(callback); w.start()
