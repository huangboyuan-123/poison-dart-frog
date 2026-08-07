"""
Panel A: 数据库菜单 / Schema 树 / 连接管理
"""
import requests
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QAction, QPixmap, QPainter
from PySide6.QtWidgets import (
    QComboBox, QDialog, QHBoxLayout, QLabel, QMenu,
    QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget, QApplication,
)

def _tint_icon(path: str, color: str = '#A9B7C6') -> QIcon:
    pm = QPixmap(path)
    if pm.isNull(): return QIcon(path)
    p = QPainter(pm); p.setCompositionMode(QPainter.CompositionMode_SourceIn)
    p.fillRect(pm.rect(), QColor(color)); p.end()
    return QIcon(pm)


from ..constants import (
    API_BASE, BG, DANGER_COLOR, ICONS_DIR, MUTED, SUCCESS_COLOR, WARNING_COLOR,
)
from ..dialogs.db_config import DbConfigDialog
from ..dialogs.table_designer import TableDesignerDialog

from ..store import _db_configs, load_db_configs, save_db_configs


class PanelAMixin:
    """Mixin providing Panel A (database tree) methods for MainWindow."""

    # ═══ A栏: 数据库菜单 ═══
    def _build_panel_a(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(4, 8, 2, 4)
        layout.setSpacing(4)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel('数据库'))
        hdr.addStretch()
        btn_style = 'QPushButton { background: transparent; border: none; padding: 2px 6px; color: #86909C; } QPushButton:hover { background: rgba(255,255,255,0.06); border-radius: 2px; color: #A9B7C6; }'
        add_btn = QPushButton('+ 新增')
        add_btn.setFixedHeight(20)
        add_btn.setStyleSheet(btn_style)
        add_btn.clicked.connect(self._add_db_dialog)
        hdr.addWidget(add_btn)
        refresh_btn = QPushButton('刷新')
        refresh_btn.setFixedHeight(20)
        refresh_btn.setStyleSheet(btn_style)
        refresh_btn.clicked.connect(self._load_schema_tree)
        hdr.addWidget(refresh_btn)
        layout.addLayout(hdr)

        self.schema_tree = QTreeWidget()
        self.schema_tree.setHeaderHidden(True)
        self.schema_tree.setIndentation(14)
        self.schema_tree.setIconSize(QSize(22, 22))
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
        del_icon = _tint_icon(str(ICONS_DIR / 'cancel.png'))
        del_btn = QPushButton(del_icon, '')
        del_btn.setFixedSize(22, 22)
        del_btn.setIconSize(QSize(16, 16))
        del_btn.setFlat(True)
        del_btn.setToolTip('删除当前连接')
        del_btn.setStyleSheet('QPushButton { background: transparent; border: none; } QPushButton:hover { background: rgba(255,255,255,0.1); border-radius: 2px; }')
        del_btn.clicked.connect(self._delete_db_config)
        conn_row.addWidget(del_btn)
        mgr_btn = QPushButton('⚙')  # gear emoji
        mgr_btn.setFixedSize(22, 22)
        mgr_btn.setToolTip('管理连接')
        mgr_btn.clicked.connect(self._add_db_dialog)
        conn_row.addWidget(mgr_btn)
        layout.addLayout(conn_row)

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
            # 更新 SQL 自动补全词表
            self._update_sql_completions()

            for db_name in dbs:
                db_item = QTreeWidgetItem([db_name])
                db_icon = _tint_icon(str(ICONS_DIR / 'big_database.png'))
                db_item.setIcon(0, db_icon)
                db_item.setData(0, Qt.UserRole + 1, 'database')
                db_item.setData(0, Qt.UserRole + 2, db_name)
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

    def _on_tree_expand(self, item: QTreeWidgetItem):
        """展开节点时懒加载"""
        node_type = item.data(0, Qt.UserRole + 1)

        if node_type == 'database':
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
                    QTreeWidgetItem(t_item, ['...'])
                    item.addChild(t_item)

            self._run_async(do_fetch, callback)

        elif node_type == 'table':
            item.takeChildren()
            columns = item.data(0, Qt.UserRole) or []
            for col in columns:
                key_info = ''
                if col.get('key') == 'MUL': key_info = ' \U0001f517'
                null = '?' if col.get('nullable') else ''
                col_text = f"{col['name']}: {col['type']}{null}{key_info}"
                col_item = QTreeWidgetItem([col_text])
                col_item.setData(0, Qt.UserRole + 1, 'column')
                col_item.setForeground(0, QColor(MUTED))
                if col.get('key') == 'PRI':
                    col_item.setIcon(0, _tint_icon(str(ICONS_DIR / 'mysql_icon' / 'key.png')))
                item.addChild(col_item)

    def _on_tree_menu(self, pos):
        """右键菜单"""
        item = self.schema_tree.itemAt(pos)
        if not item:
            return
        node_type = item.data(0, Qt.UserRole + 1)

        if node_type == 'table':
            table_name = str(item.text(0))
            db_name = str(item.data(0, Qt.UserRole + 2) or '')
            columns = item.data(0, Qt.UserRole) or []

            menu = QMenu(self)
            a1 = QAction('查看表结构', self)
            a1.triggered.connect(lambda _t=table_name, _c=columns: self._show_table_structure(_t, _c))
            menu.addAction(a1)
            a3 = QAction('\U0001f4d0 设计表 (可视化)', self)  # design emoji
            a3.triggered.connect(lambda _d=db_name, _t=table_name, _c=columns: self._open_table_designer(_d, _t, _c))
            menu.addAction(a3)
            menu.addSeparator()
            a5 = QAction('\U0001f5d1 删除表', self)  # trash emoji
            a5.triggered.connect(lambda _d=db_name, _t=table_name: self._drop_table(_d, _t))
            menu.addAction(a5)
            a6 = QAction('复制表名', self)
            a6.triggered.connect(lambda _t=table_name: QApplication.clipboard().setText(_t))
            menu.addAction(a6)
            menu.exec(self.schema_tree.mapToGlobal(pos))

        elif node_type == 'database':
            db_name = str(item.data(0, Qt.UserRole + 2) or '')
            menu = QMenu(self)
            a1 = QAction('刷新', self); a1.triggered.connect(self._load_schema_tree); menu.addAction(a1)
            menu.addSeparator()
            a2 = QAction('\U0001f5d1 删除数据库', self)
            a2.triggered.connect(lambda _d=db_name: self._drop_database(_d))
            menu.addAction(a2)
            a3 = QAction('复制库名', self)
            a3.triggered.connect(lambda _d=db_name: QApplication.clipboard().setText(_d))
            menu.addAction(a3)
            menu.exec(self.schema_tree.mapToGlobal(pos))

    def _show_table_structure(self, table_name: str, columns: list):
        """右键查看表结构 → 新建Tab"""
        rows = [[c.get('name', ''), c.get('type', ''), c.get('key', ''),
                 'YES' if c.get('nullable') else 'NO', str(c.get('default', ''))] for c in columns]
        idx = self._add_data_tab(f'\U0001f50d {table_name}', ['字段', '类型', '键', '可空', '默认值'], rows)
        self._render_tab_page(idx)
        self.rb_type.setText(f'结构: {table_name}')
        self.rb_elapsed.setText('')
        self.rb_rows.setText(f'{len(columns)} 字段')
        self.rb_status.setText('')
        self.rb_status.setStyleSheet('')

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

    def _open_table_designer(self, db: str, table: str, columns: list):
        """打开可视化表设计器"""
        dlg = TableDesignerDialog(db, table, columns, self)
        if dlg.exec() == QDialog.Accepted:
            self._reload_current_tab()
            self._load_schema_tree()

    def _drop_table(self, db: str, table: str):
        """删除表"""
        reply = QMessageBox.warning(self, '⚠️ 危险操作',
                                     f'确定要删除表 {db}.{table} 吗？\n\n此操作不可逆！',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        reply2 = QMessageBox.warning(self, '⚠️ 再次确认',
                                      f'输入 YES 确认删除 {db}.{table}',
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply2 != QMessageBox.Yes:
            return
        try:
            r = requests.delete(f'{API_BASE}/api/table/drop?database={db}&table={table}', timeout=10).json()
            if r.get('success'):
                self._show_log(f'✓ {r["message"]}')
                self._load_schema_tree()
            else:
                self._show_log(f'✗ {r.get("detail", "删除失败")}')
        except Exception as e:
            self._show_log(f'✗ 删除失败: {e}')

    def _drop_database(self, db: str):
        """删除数据库"""
        reply = QMessageBox.warning(self, '⚠️ 危险操作',
                                     f'确定要删除数据库 {db} 吗？\n\n所有表和数据将永久丢失！',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        reply2 = QMessageBox.warning(self, '⚠️ 再次确认',
                                      f'输入 YES 确认删除数据库 {db}',
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply2 != QMessageBox.Yes:
            return
        try:
            r = requests.delete(f'{API_BASE}/api/table/database/drop?database={db}', timeout=10).json()
            if r.get('success'):
                self._show_log(f'✓ {r["message"]}')
                self._load_schema_tree()
            else:
                self._show_log(f'✗ {r.get("detail", "删除失败")}')
        except Exception as e:
            self._show_log(f'✗ 删除失败: {e}')

    # ── DB 连接管理 ─────────────────────────
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

    def _delete_db_config(self):
        """删除当前选中的数据库连接"""
        if not _db_configs:
            return
        idx = self.sidebar_combo.currentIndex()
        if idx < 0 or idx >= len(_db_configs):
            return
        cfg = _db_configs[idx]
        reply = QMessageBox.question(self, '确认删除',
                                      f'确定删除连接 "{cfg["name"]}" 吗？')
        if reply != QMessageBox.Yes:
            return
        del _db_configs[idx]
        save_db_configs()
        self._refresh_db_combo()
        self._load_schema_tree()

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

    def _update_sql_completions(self):
        """收集所有表名/列名 + SQL关键字用于自动补全"""
        words = set()
        for i in range(self.schema_tree.topLevelItemCount()):
            db_item = self.schema_tree.topLevelItem(i)
            for j in range(db_item.childCount()):
                tbl_item = db_item.child(j)
                table_name = tbl_item.text(0)
                words.add(table_name)
                for k in range(tbl_item.childCount()):
                    col_item = tbl_item.child(k)
                    if col_item.text(0) != '...':
                        col_name = col_item.text(0).split(':')[0]
                        words.add(col_name)
        words.update(['SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN',
                       'LIKE', 'BETWEEN', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'ON',
                       'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET',
                       'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP',
                       'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'AS',
                       'NULL', 'IS NULL', 'IS NOT NULL', 'DEFAULT', 'PRIMARY KEY',
                       'LIMIT 100', 'ORDER BY', 'DESC', 'ASC'])
        self.sql_completion_words = sorted(words)
