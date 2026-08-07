"""
数据库配置存储 & 历史记录
"""
import json
from typing import Any, Dict, List

from .constants import DB_CONFIG_FILE, HISTORY_FILE

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
