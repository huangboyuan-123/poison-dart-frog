"""
箭毒蛙 — Redis 专用版 配色 & 常量
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
ACCENT_COLOR = '#00BFA5'
GRADIENT_START = '#00BFA5'
GRADIENT_MID = '#00E676'
GRADIENT_END = '#00B0FF'

REDIS_CONFIG_FILE = Path(__file__).parent.parent.parent.parent / '.redis_configs.json'
HISTORY_FILE = Path.home() / '.dendrobates_history.json'
ENV_FILE = Path(__file__).parent.parent.parent.parent / '.env'
