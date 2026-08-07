"""
AI 设置弹窗
"""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout,
)

from ..constants import ENV_FILE


class SettingsDialog(QDialog):
    """AI 密钥/模型设置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('AI 设置')
        self.setMinimumWidth(480)
        self._build_ui()
        self._load_env()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        layout.addWidget(QLabel('<b>LLM API 配置</b>'))
        layout.addWidget(QLabel('修改后重启后端生效'))

        self.fields = {}
        field_defs = [
            ('DEEPSEEK_API_KEY', 'DeepSeek 密钥', True),
            ('OPENAI_API_KEY', 'OpenAI 密钥 (备用)', True),
            ('LLM_BASE_URL', 'API 地址', False),
            ('LLM_MODEL', '模型名称', False),
        ]

        form = QFormLayout()
        for key, label, is_pwd in field_defs:
            edit = QLineEdit()
            if is_pwd:
                edit.setEchoMode(QLineEdit.Password)
                show_btn = QPushButton('\U0001f441')  # eye emoji
                show_btn.setFixedSize(28, 28)
                show_btn.setCheckable(True)
                show_btn.toggled.connect(lambda checked, e=edit: e.setEchoMode(
                    QLineEdit.Normal if checked else QLineEdit.Password))
                row = QHBoxLayout()
                row.addWidget(edit, 1)
                row.addWidget(show_btn)
                form.addRow(label, row)
            else:
                form.addRow(label, edit)
            self.fields[key] = edit
        layout.addLayout(form)

        # 保存/取消
        btns = QHBoxLayout()
        btns.addStretch()
        save_btn = QPushButton('保存到 .env')
        save_btn.setProperty('accent', True)
        save_btn.clicked.connect(self._save_env)
        btns.addWidget(save_btn)
        btns.addWidget(QPushButton('取消', clicked=self.reject))
        layout.addLayout(btns)

    def _load_env(self):
        """从 .env 和环境变量读取当前值"""
        import os as _os
        env_vars = {}
        if ENV_FILE.exists():
            for line in ENV_FILE.read_text('utf-8').split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")

        for key, edit in self.fields.items():
            val = _os.getenv(key, '') or env_vars.get(key, '')
            edit.setText(val)

    def _save_env(self):
        """保存到 .env 文件"""
        # 读取现有内容
        lines = []
        if ENV_FILE.exists():
            lines = ENV_FILE.read_text('utf-8').split('\n')

        # 更新或追加每个字段
        updated = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                for key in self.fields:
                    if stripped.startswith(f'{key}=') or stripped.startswith(f'{key} ='):
                        new_lines.append(f'{key}={self.fields[key].text()}')
                        updated.add(key)
                        break
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # 追加未更新的字段
        for key, edit in self.fields.items():
            if key not in updated:
                new_lines.append(f'{key}={edit.text()}')
                updated.add(key)

        ENV_FILE.write_text('\n'.join(new_lines), 'utf-8')
        QMessageBox.information(self, '已保存', '设置已保存到 .env 文件。\n请重启后端 (uvicorn) 使配置生效。')
        self.accept()
