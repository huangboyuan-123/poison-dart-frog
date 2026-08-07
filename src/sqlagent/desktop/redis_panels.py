"""
Redis 面板: 键浏览、值查看、AI命令生成/执行
"""
from typing import Dict

import json
import re
import requests
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMenu, QMessageBox, QPlainTextEdit, QPushButton,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .constants import (
    API_BASE, ICONS_DIR, MUTED,
)
from .workers import ApiWorker


class RedisPanelsMixin:
    """Mixin providing Redis panel methods for MainWindow."""

    # ═══ Redis Panel A: 键浏览 ═══
    def _build_redis_panel_a(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(4, 8, 2, 4)
        layout.setSpacing(4)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel('\U0001f534 Redis 键'))  # red circle
        hdr.addStretch()
        refresh_btn = QPushButton('刷新')
        refresh_btn.setFixedHeight(22)
        refresh_btn.clicked.connect(self._load_redis_keys)
        hdr.addWidget(refresh_btn)
        layout.addLayout(hdr)

        self.redis_key_input = QLineEdit()
        self.redis_key_input.setPlaceholderText('键模式 (如 user:*, * 查全部)')
        self.redis_key_input.returnPressed.connect(self._load_redis_keys)
        layout.addWidget(self.redis_key_input)

        self.redis_tree = QTreeWidget()
        self.redis_tree.setHeaderHidden(True)
        self.redis_tree.setIndentation(12)
        self.redis_tree.itemClicked.connect(self._on_redis_key_click)
        self.redis_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.redis_tree.customContextMenuRequested.connect(self._on_redis_tree_menu)
        layout.addWidget(self.redis_tree, 1)

    def _build_redis_panel_b(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(4, 8, 8, 4)
        layout.setSpacing(4)

        self.redis_key_label = QLabel('选择一个键查看值')
        self.redis_key_label.setStyleSheet('font-weight: bold; font-size: 13px;')
        layout.addWidget(self.redis_key_label)

        type_row = QHBoxLayout()
        self.redis_type_label = QLabel('')
        self.redis_type_label.setStyleSheet(f'color: {MUTED};')
        type_row.addWidget(self.redis_type_label)
        type_row.addStretch()
        layout.addLayout(type_row)

        self.redis_value_text = QTextEdit()
        self.redis_value_text.setReadOnly(True)
        self.redis_value_text.setFont(QFont('Consolas', 10))
        layout.addWidget(self.redis_value_text, 1)

        save_row = QHBoxLayout()
        save_icon = QIcon(str(ICONS_DIR / 'diskette.png'))
        self.redis_save_btn = QPushButton(save_icon, '保存修改')
        self.redis_save_btn.setProperty('accent', True)
        self.redis_save_btn.clicked.connect(self._save_redis_value)
        self.redis_save_btn.setEnabled(False)
        save_row.addWidget(self.redis_save_btn)
        save_row.addStretch()
        self.redis_delete_btn = QPushButton('删除键')
        self.redis_delete_btn.setProperty('danger', True)
        self.redis_delete_btn.clicked.connect(self._delete_redis_key)
        self.redis_delete_btn.setEnabled(False)
        save_row.addWidget(self.redis_delete_btn)
        layout.addLayout(save_row)

    # ═══ Redis Panel C: AI 助手 ═══
    def _build_redis_panel_c(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(4, 8, 8, 4)
        layout.setSpacing(6)

        nl_group = QGroupBox('Redis 自然语言')
        nl_ly = QVBoxLayout(nl_group)
        self.redis_input = QPlainTextEdit()
        self.redis_input.setPlaceholderText('用中文描述 Redis 操作...\n例: 查看所有user:开头的键、设置缓存key过期时间')
        self.redis_input.setMaximumHeight(80)
        nl_ly.addWidget(self.redis_input)
        btn_row = QHBoxLayout()
        self.redis_gen_btn = QPushButton('生成命令')
        self.redis_gen_btn.setProperty('accent', True)
        self.redis_gen_btn.clicked.connect(self._redis_generate)
        btn_row.addWidget(self.redis_gen_btn)
        btn_row.addWidget(QPushButton('清空', clicked=lambda: self.redis_input.clear()))
        btn_row.addStretch()
        nl_ly.addLayout(btn_row)
        layout.addWidget(nl_group)

        cmd_group = QGroupBox('Redis 命令预览')
        cmd_ly = QVBoxLayout(cmd_group)
        self.redis_cmd_text = QTextEdit()
        self.redis_cmd_text.setPlaceholderText('-- AI 生成的 Redis 命令将显示在这里')
        self.redis_cmd_text.setReadOnly(True)
        self.redis_cmd_text.setFont(QFont('Consolas', 10))
        cmd_ly.addWidget(self.redis_cmd_text)
        exec_row = QHBoxLayout()
        self.redis_exec_btn = QPushButton('执行命令')
        self.redis_exec_btn.setProperty('accent', True)
        self.redis_exec_btn.clicked.connect(self._redis_execute)
        exec_row.addWidget(self.redis_exec_btn)
        exec_row.addStretch()
        cmd_ly.addLayout(exec_row)
        layout.addWidget(cmd_group, 1)

        self.redis_log = QTextEdit()
        self.redis_log.setReadOnly(True)
        self.redis_log.setMaximumHeight(120)
        self.redis_log.setFont(QFont('Consolas', 10))
        layout.addWidget(self.redis_log)

    # ── Redis 数据加载 ──────────────────────
    def _load_redis_keys(self):
        """加载 Redis 键列表"""
        pattern = self.redis_key_input.text() or '*'
        self.redis_tree.clear()

        def do_fetch():
            try:
                r = requests.get(f'{API_BASE}/api/redis/keys?pattern={pattern}', timeout=5)
                return r.json()
            except Exception as e:
                return {'error': str(e)}

        def callback(data):
            keys = data.get('keys', [])
            tree_map: Dict[str, QTreeWidgetItem] = {}
            for key in sorted(keys):
                parts = key.split(':')
                for i, part in enumerate(parts):
                    full_path = ':'.join(parts[:i+1])
                    if i == len(parts) - 1:
                        item = QTreeWidgetItem([part])
                        item.setData(0, Qt.UserRole + 1, 'key')
                        item.setToolTip(0, str(key))
                        type_color = data.get('types', {}).get(key, '')
                        if type_color:
                            item.setForeground(0, QColor(type_color))
                        parent_path = ':'.join(parts[:i]) if i > 0 else ''
                        if parent_path and parent_path in tree_map:
                            tree_map[parent_path].addChild(item)
                        else:
                            self.redis_tree.addTopLevelItem(item)
                    else:
                        if full_path not in tree_map:
                            item = QTreeWidgetItem([part])
                            parent_path = ':'.join(parts[:i]) if i > 0 else ''
                            if parent_path and parent_path in tree_map:
                                tree_map[parent_path].addChild(item)
                            else:
                                self.redis_tree.addTopLevelItem(item)
                            tree_map[full_path] = item

        self._run_async(do_fetch, callback)

    def _on_redis_tree_menu(self, pos):
        """Redis 树右键菜单"""
        item = self.redis_tree.itemAt(pos)
        if not item or item.data(0, Qt.UserRole + 1) != 'key':
            return
        key = item.toolTip(0)
        menu = QMenu(self)
        act_del = QAction('\U0001f5d1 删除键', self)  # trash
        act_del.triggered.connect(lambda _k=key: self._delete_redis_key_by_name(_k))
        menu.addAction(act_del)
        act_copy = QAction('复制键名', self)
        act_copy.triggered.connect(lambda _k=key: QApplication.clipboard().setText(_k))
        menu.addAction(act_copy)
        menu.exec(self.redis_tree.mapToGlobal(pos))

    def _delete_redis_key_by_name(self, key: str):
        """通过键名删除 Redis 键（先确认存在）"""
        try:
            check = requests.get(f'{API_BASE}/api/redis/key/{key}', timeout=3).json()
            if 'detail' in check:
                QMessageBox.warning(self, '提示', f'键 {key} 不存在')
                return
        except Exception:
            pass

        reply = QMessageBox.warning(self, '⚠️ 确认删除',
                                     f'确定删除键 {key} 吗？\n类型: {check.get("type", "?")}\n值: {str(check.get("value",""))[:50]}',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                r = requests.delete(f'{API_BASE}/api/redis/key/{key}', timeout=5).json()
                if r.get('ok'):
                    self.redis_value_text.clear()
                    self._load_redis_keys()
                    self._show_log(f'✓ 已删除键: {key}')
                else:
                    self._show_log(f'✗ 删除失败')
            except Exception as e:
                self._show_log(f'✗ 删除失败: {e}')

    def _on_redis_key_click(self, item: QTreeWidgetItem, _col: int):
        if item.data(0, Qt.UserRole + 1) != 'key':
            return
        key = item.toolTip(0)
        self.redis_key_label.setText(f'键: {key}')
        self.redis_value_text.setReadOnly(True)
        self.redis_save_btn.setEnabled(False)
        self.redis_delete_btn.setEnabled(False)

        def do_fetch():
            try:
                r = requests.get(f'{API_BASE}/api/redis/key/{key}', timeout=5)
                return r.json()
            except Exception as e:
                return {'error': str(e)}

        def callback(data):
            if data.get('error'):
                self.redis_value_text.setPlainText(f"// 错误: {data['error']}")
                return
            self.redis_type_label.setText(f'类型: {data.get("type", "?")}')
            value = data.get('value', '')
            t = data.get('type', 'string')
            # Hash → 字段表格
            if t == 'hash' and isinstance(value, dict):
                lines = [f'{"Field":<20} Value', '-' * 50]
                for k, v in value.items():
                    v_str = str(v)
                    if isinstance(v_str, str) and (v_str.startswith('{') or v_str.startswith('[')):
                        try:
                            c = re.sub(r'(\d+)L\b', r'\1', v_str).replace('None','null').replace('True','true').replace('False','false')
                            v_str = json.dumps(json.loads(c), indent=2, ensure_ascii=False)
                        except: pass
                    lines.append(f'{k:<20} {v_str}')
                value = '\n'.join(lines)
            # String → JSON格式化
            elif isinstance(value, str):
                try:
                    clean = re.sub(r'(\d+)L\b', r'\1', value)
                    clean = clean.replace('None', 'null').replace('True', 'true').replace('False', 'false')
                    value = json.dumps(json.loads(clean), indent=2, ensure_ascii=False)
                except (json.JSONDecodeError, ValueError):
                    pass
            self.redis_value_text.setPlainText(str(value) if value is not None else '(nil)')
            self.redis_value_text.setReadOnly(False)
            self.redis_save_btn.setEnabled(True)
            self.redis_delete_btn.setEnabled(True)

        self._run_async(do_fetch, callback)

    def _save_redis_value(self):
        key = self.redis_key_label.text().replace('键: ', '')
        val = self.redis_value_text.toPlainText()
        try:
            r = requests.post(f'{API_BASE}/api/redis/key/{key}',
                              json={'value': val}, timeout=5).json()
            if r.get('ok'):
                QMessageBox.information(self, '成功', '已保存')
            else:
                QMessageBox.warning(self, '错误', str(r.get('error', '')))
        except Exception as e:
            QMessageBox.warning(self, '错误', str(e))

    def _delete_redis_key(self):
        key = self.redis_key_label.text().replace('键: ', '')
        if QMessageBox.question(self, '确认', f'删除键 {key}?'):
            try:
                r = requests.delete(f'{API_BASE}/api/redis/key/{key}', timeout=5).json()
                if r.get('ok'):
                    self.redis_value_text.clear()
                    self._load_redis_keys()
            except Exception as e:
                QMessageBox.warning(self, '错误', str(e))

    def _redis_generate(self):
        question = self.redis_input.toPlainText().strip()
        if not question:
            return
        self.redis_gen_btn.setText('生成中...')
        self.redis_gen_btn.setEnabled(False)

        def do_fetch():
            try:
                r = requests.post(f'{API_BASE}/api/redis/query',
                                  json={'question': question}, timeout=60)
                return r.json()
            except Exception as e:
                return {'error': str(e)}

        def callback(resp):
            self.redis_gen_btn.setText('生成命令')
            self.redis_gen_btn.setEnabled(True)
            if resp.get('error'):
                self.redis_cmd_text.setPlainText(f'# 错误: {resp["error"]}')
            else:
                self.redis_cmd_text.setPlainText(resp.get('command', resp.get('answer', '')))
            self.redis_log.append(f'[Q] {question}\n[A] {resp.get("command", resp.get("answer", ""))}\n')

        self._run_async(do_fetch, callback)

    def _execute_redis_cmd(self, cmd: str):
        """在 Redis 工作区执行命令"""
        self.exec_btn.setText('执行中...')
        self.exec_btn.setEnabled(False)
        try:
            r = requests.post(f'{API_BASE}/api/redis/execute',
                              json={'command': cmd}, timeout=10).json()
            if r.get('ok'):
                self._show_log(f'✓ {r.get("result", "OK")}')
                self._show_redis_result(r.get('result', ''), cmd)
                self._load_redis_keys()
            else:
                self._show_log(f'✗ {r.get("error")}')
        except Exception as e:
            self._show_log(f'✗ {e}')
        finally:
            self.exec_btn.setText('执行 SQL')
            self.exec_btn.setEnabled(True)

    def _redis_execute(self):
        cmd_text = self.redis_cmd_text.toPlainText().strip()
        if not cmd_text or cmd_text.startswith('#'):
            return
        self.redis_exec_btn.setText('执行中...')
        self.redis_exec_btn.setEnabled(False)

        def do_fetch():
            try:
                r = requests.post(f'{API_BASE}/api/redis/execute',
                                  json={'command': cmd_text}, timeout=10)
                return r.json()
            except Exception as e:
                return {'error': str(e)}

        def callback(resp):
            self.redis_exec_btn.setText('执行命令')
            self.redis_exec_btn.setEnabled(True)
            if resp.get('ok'):
                result = resp.get('result', 'OK')
                self.redis_log.append(f'✓ {result}\n')
                self._show_redis_result(result, cmd_text)
                self._load_redis_keys()
            else:
                self.redis_log.append(f'✗ {resp.get("error")}\n')

        self._run_async(do_fetch, callback)

    def _show_redis_result(self, result: str, cmd: str):
        """解析 Redis 执行结果并展示到 B栏"""
        lines = result.strip().split('\n')
        for line in lines:
            if 'GET:' in line or 'HGET:' in line or 'HGETALL:' in line or 'LRANGE:' in line or 'SMEMBERS:' in line or 'ZRANGE:' in line:
                val = line.split(':', 1)[-1].strip()
                self.redis_value_text.setPlainText(val)
                parts = cmd.strip().split()
                if len(parts) >= 2:
                    self.redis_key_label.setText(f'键: {parts[1]} (AI查询)')
                break
