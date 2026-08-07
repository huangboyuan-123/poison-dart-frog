"""
Redis 对话框 — 连接配置 + 新建键 + TTL设置
"""
import json
from datetime import datetime
from typing import Any, Dict, List

from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout,
                                QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                                QPushButton, QSpinBox, QComboBox, QVBoxLayout,
                                QTableWidget, QTableWidgetItem)
from PySide6.QtCore import Qt
import requests

from .constants import API_BASE, REDIS_CONFIG_FILE


# Redis 配置存储
_redis_configs: List[Dict[str, Any]] = []


def load_redis_configs():
    global _redis_configs
    try:
        if REDIS_CONFIG_FILE.exists():
            _redis_configs = json.loads(REDIS_CONFIG_FILE.read_text('utf-8'))
    except Exception:
        _redis_configs = []


def save_redis_configs():
    REDIS_CONFIG_FILE.write_text(json.dumps(_redis_configs, ensure_ascii=False, indent=2), 'utf-8')


class RedisConnDialog(QDialog):
    """Redis 连接配置弹窗"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Redis 连接配置')
        self.setMinimumWidth(420)
        layout = QFormLayout(self)
        layout.setSpacing(8)

        self.name_edit = QLineEdit(); self.name_edit.setPlaceholderText('我的Redis')
        layout.addRow('名称:', self.name_edit)
        self.host_edit = QLineEdit('localhost'); layout.addRow('地址:', self.host_edit)
        self.port_spin = QSpinBox(); self.port_spin.setRange(1, 65535); self.port_spin.setValue(6379)
        layout.addRow('端口:', self.port_spin)
        self.pass_edit = QLineEdit(); self.pass_edit.setEchoMode(QLineEdit.Password)
        layout.addRow('密码:', self.pass_edit)
        self.db_spin = QSpinBox(); self.db_spin.setRange(0, 15); layout.addRow('DB:', self.db_spin)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def get_config(self) -> Dict[str, Any]:
        return {
            'id': datetime.now().strftime('%Y%m%d%H%M%S'),
            'name': self.name_edit.text() or '默认',
            'host': self.host_edit.text(), 'port': self.port_spin.value(),
            'password': self.pass_edit.text(), 'db': self.db_spin.value(),
        }


class NewKeyDialog(QDialog):
    """新建 Redis 键弹窗"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('新建键')
        self.setMinimumWidth(380)
        layout = QFormLayout(self)
        self.key_edit = QLineEdit(); layout.addRow('键名:', self.key_edit)
        self.type_combo = QComboBox()
        self.type_combo.addItems(['string', 'hash', 'list', 'set', 'zset'])
        layout.addRow('类型:', self.type_combo)
        self.val_edit = QLineEdit(); self.val_edit.setPlaceholderText('string: 值; hash: f1=v1 f2=v2; list: v1 v2; set: v1 v2')
        layout.addRow('初始值:', self.val_edit)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def get_data(self):
        return self.key_edit.text(), self.type_combo.currentText(), self.val_edit.text()


class TTLDialog(QDialog):
    """设置 TTL 弹窗"""
    def __init__(self, key: str, current_ttl: int, parent=None):
        super().__init__(parent)
        self.key = key
        self.setWindowTitle(f'TTL - {key}')
        layout = QFormLayout(self)
        layout.addRow(QLabel(f'键: {key}'))
        layout.addRow(QLabel(f'当前 TTL: {current_ttl}s' if current_ttl > 0 else '当前 TTL: 永久'))
        self.ttl_spin = QSpinBox(); self.ttl_spin.setRange(-1, 999999)
        self.ttl_spin.setSpecialValueText('永久(-1)'); self.ttl_spin.setValue(current_ttl if current_ttl > 0 else -1)
        layout.addRow('TTL(秒):', self.ttl_spin)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def get_ttl(self):
        return self.ttl_spin.value()
