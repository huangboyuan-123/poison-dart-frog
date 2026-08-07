"""
数据库连接配置弹窗
"""
from datetime import datetime
from typing import Any, Dict

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
)


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
            'database': '',  # 不指定库，连接服务器根级别
        }
