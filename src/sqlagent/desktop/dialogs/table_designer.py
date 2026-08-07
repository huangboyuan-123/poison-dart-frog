"""
表设计器弹窗 + 圆角容器控件
"""
from typing import Any, Dict, List

import requests
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QBrush
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..constants import API_BASE, ICONS_DIR


class _RoundedWidget(QWidget):
    """带抗锯齿圆角的容器"""

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 10, 10)
        p.fillPath(path, QBrush(QColor('#2B2B2B')))
        p.setClipPath(path)

    def resizeEvent(self, event):
        self.update()
        super().resizeEvent(event)


class TableDesignerDialog(QDialog):
    """可视化表结构编辑器"""

    def __init__(self, db_name: str, table_name: str, columns: List[Dict], parent=None):
        super().__init__(parent)
        self.db_name = db_name
        self.table_name = table_name
        self.orig_columns = columns  # 原始列信息
        self.setWindowTitle(f'设计表: {db_name}.{table_name}')
        self.setMinimumSize(700, 400)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'<b>{self.db_name}.{self.table_name}</b> — 双击单元格编辑'))

        # 可编辑表格
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(['列名', '类型', '可空', '默认值', '键(PRI/UNI/MUL)'])
        self.tbl.horizontalHeader().setStretchLastSection(True)
        self._load_columns()
        layout.addWidget(self.tbl, 1)

        # 按钮
        btn_row = QHBoxLayout()
        add_btn = QPushButton('+ 添加列')
        add_btn.clicked.connect(self._add_column)
        btn_row.addWidget(add_btn)
        del_btn = QPushButton('🗑 删除选中列')
        del_btn.clicked.connect(self._delete_column)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        save_icon = QIcon(str(ICONS_DIR / 'diskette.png'))
        save_btn = QPushButton(save_icon, '保存修改')
        save_btn.setProperty('accent', True)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _load_columns(self):
        self.tbl.setRowCount(len(self.orig_columns))
        for r, col in enumerate(self.orig_columns):
            items = [
                QTableWidgetItem(col.get('name', '')),
                QTableWidgetItem(col.get('type', '')),
                QTableWidgetItem('YES' if col.get('nullable') else 'NO'),
                QTableWidgetItem(str(col.get('default', '')) if col.get('default') else ''),
                QTableWidgetItem(col.get('key', '')),
            ]
            for c, item in enumerate(items):
                self.tbl.setItem(r, c, item)

    def _add_column(self):
        row = self.tbl.rowCount()
        self.tbl.insertRow(row)
        defaults = ['new_col', 'VARCHAR(255)', 'YES', '', '']
        for c, val in enumerate(defaults):
            self.tbl.setItem(row, c, QTableWidgetItem(val))

    def _delete_column(self):
        for r in set(i.row() for i in self.tbl.selectedItems()):
            col_name = self.tbl.item(r, 0).text() if self.tbl.item(r, 0) else ''
            reply = QMessageBox.question(self, '确认', f'删除列 {col_name}？此操作不可逆！')
            if reply == QMessageBox.Yes:
                self.tbl.removeRow(r)

    def _save(self):
        # 收集当前列定义
        new_cols = []
        for r in range(self.tbl.rowCount()):
            name = self.tbl.item(r, 0).text() if self.tbl.item(r, 0) else ''
            dtype = self.tbl.item(r, 1).text() if self.tbl.item(r, 1) else ''
            nullable = (self.tbl.item(r, 2).text() if self.tbl.item(r, 2) else 'YES') == 'YES'
            default = self.tbl.item(r, 3).text() if self.tbl.item(r, 3) else ''
            key = self.tbl.item(r, 4).text() if self.tbl.item(r, 4) else ''
            if name:
                new_cols.append({'name': name, 'type': dtype, 'nullable': nullable,
                                 'default': default, 'key': key})

        # 生成 ALTER 语句
        orig_names = {c['name'] for c in self.orig_columns}
        new_names = {c['name'] for c in new_cols}
        added = [c for c in new_cols if c['name'] not in orig_names]
        removed = [c for c in self.orig_columns if c['name'] not in new_names]
        modified = [c for c in new_cols if c['name'] in orig_names]

        sqls = []
        for c in added:
            null = '' if c['nullable'] else ' NOT NULL'
            dflt = f" DEFAULT '{c['default']}'" if c['default'] else ''
            sqls.append(f"ALTER TABLE `{self.db_name}`.`{self.table_name}` ADD COLUMN `{c['name']}` {c['type']}{null}{dflt}")

        for c in removed:
            sqls.append(f"ALTER TABLE `{self.db_name}`.`{self.table_name}` DROP COLUMN `{c['name']}`")

        for c in modified:
            orig = next((o for o in self.orig_columns if o['name'] == c['name']), None)
            if orig and (c['type'] != orig.get('type', '') or
                         c['nullable'] != orig.get('nullable', True) or
                         str(c.get('default', '')) != str(orig.get('default', ''))):
                null = '' if c['nullable'] else ' NOT NULL'
                dflt = f" DEFAULT '{c['default']}'" if c['default'] else ''
                sqls.append(f"ALTER TABLE `{self.db_name}`.`{self.table_name}` MODIFY COLUMN `{c['name']}` {c['type']}{null}{dflt}")

        if not sqls:
            QMessageBox.information(self, '提示', '没有变更')
            return

        preview = '\n'.join(sqls[:5])
        if len(sqls) > 5:
            preview += f'\n... 共 {len(sqls)} 条 ALTER 语句'
        reply = QMessageBox.question(self, '确认执行', f'将执行:\n{preview}\n\n确定？')
        if reply != QMessageBox.Yes:
            return

        # 执行
        errors = []
        for s in sqls:
            try:
                r = requests.post(f'{API_BASE}/api/execute',
                                  json={'sql': s, 'read_only': False}, timeout=10).json()
                if not r.get('success'):
                    errors.append(f'{s}: {r.get("error")}')
            except Exception as e:
                errors.append(f'{s}: {e}')

        if errors:
            QMessageBox.warning(self, '部分失败', '\n'.join(errors[:5]))
        else:
            QMessageBox.information(self, '成功', f'已执行 {len(sqls)} 条 ALTER 语句')
            self.accept()
