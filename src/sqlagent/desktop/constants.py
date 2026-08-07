"""
配色 & 常量
"""
from pathlib import Path

API_BASE = 'http://localhost:8000'
ICONS_DIR = Path(__file__).parent.parent / 'static'
BG = '#2B2B2B'
PANEL = '#3C3F41'
INPUT_BG = '#3C3F41'
MUTED = '#808080'
SUCCESS_COLOR = '#6A8759'
DANGER_COLOR = '#BC3F3C'
WARNING_COLOR = '#CC7832'
ACCENT_COLOR = '#8B3A3A'
GRADIENT_START = '#5C1A1A'
GRADIENT_MID = '#8B3A3A'
GRADIENT_END = '#3C0A0A'

DB_CONFIG_FILE = Path(__file__).parent.parent.parent.parent / '.db_configs.json'
HISTORY_FILE = Path.home() / '.sqlagent_history.json'

DANGER_KW = ['DROP TABLE', 'DROP DATABASE', 'TRUNCATE', 'DELETE FROM']

ENV_FILE = Path(__file__).parent.parent.parent.parent / '.env'
