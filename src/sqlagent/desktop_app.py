"""
SQLAgent Desktop — Tkinter 桌面端
Python 内置 GUI，零额外依赖
运行: python src/sqlagent/desktop_app.py
"""
import json
import os
import re
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Dict, List, Optional

import requests

# ═══════════════════════════════════════════
# 配色 & 常量
# ═══════════════════════════════════════════
BG = '#1E2128'
PANEL = '#272B33'
INPUT_BG = '#2F343D'
ACCENT = '#2574FF'
WHITE = '#E8E8E8'
GRAY = '#86909C'
MUTED = '#5A6270'
DANGER = '#E05555'
SUCCESS = '#3FB950'
WARNING = '#D29922'
FONT = ('Consolas', 10)
FONT_SM = ('Consolas', 9)
API_BASE = 'http://localhost:8000'
HISTORY_FILE = Path.home() / '.sqlagent_history.json'

# 高危 SQL 关键字
DANGER_KW = ['DROP TABLE', 'DROP DATABASE', 'TRUNCATE', 'DELETE FROM']

# ═══════════════════════════════════════════
# 数据库配置存储
# ═══════════════════════════════════════════
DB_CONFIGS: List[Dict[str, Any]] = []
CURRENT_DB: Optional[Dict[str, Any]] = None

DB_CONFIG_FILE = Path(__file__).parent.parent.parent / '.db_configs.json'

def load_db_configs():
    global DB_CONFIGS
    try:
        if DB_CONFIG_FILE.exists():
            DB_CONFIGS = json.loads(DB_CONFIG_FILE.read_text('utf-8'))
    except Exception:
        DB_CONFIGS = []

def save_db_configs():
    DB_CONFIG_FILE.write_text(json.dumps(DB_CONFIGS, ensure_ascii=False, indent=2), 'utf-8')

def load_history():
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text('utf-8'))
    except Exception:
        pass
    return []

def save_history(items):
    HISTORY_FILE.write_text(json.dumps(items[-200:], ensure_ascii=False, indent=2), 'utf-8')

# ═══════════════════════════════════════════
# 异步 HTTP 调用 (后台线程 + root.after)
# ═══════════════════════════════════════════
def run_async(target, callback, *args):
    """在后台线程执行 target(*args)，完成后在主线程调用 callback(result)。"""
    def wrapper():
        try:
            result = target(*args)
            app.root.after(0, callback, result)
        except Exception as e:
            app.root.after(0, callback, {'error': str(e)})
    threading.Thread(target=wrapper, daemon=True).start()

# ═══════════════════════════════════════════
# 语法高亮
# ═══════════════════════════════════════════
SQL_KW = [
    'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
    'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS', 'GROUP BY',
    'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'INSERT', 'INTO',
    'VALUES', 'UPDATE', 'SET', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TABLE',
    'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'EXPLAIN', 'INDEX',
    'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'NULL', 'NOT NULL',
    'DEFAULT', 'AUTO_INCREMENT', 'CASCADE', 'INFORMATION_SCHEMA',
    'TABLE_NAME', 'COLUMN_NAME', 'DATE_SUB', 'DATE_ADD', 'NOW',
    'VARCHAR', 'INT', 'BIGINT', 'DECIMAL', 'TEXT', 'DATETIME', 'TIMESTAMP',
    'CHARACTER', 'COLLATE', 'ENGINE', 'INNODB', 'IF', 'EXISTS', 'SHOW',
    'DESCRIBE', 'USE', 'GRANT', 'REVOKE', 'TRUNCATE', 'RENAME', 'REPLACE',
    'MERGE', 'ASC', 'DESC', 'IS', 'BETWEEN', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
]

def highlight_sql(text_widget, sql):
    """在 Text widget 中渲染高亮 SQL。"""
    text_widget.config(state='normal')
    text_widget.delete('1.0', 'end')

    # 先插入原始文本
    text_widget.insert('1.0', sql)

    # 字符串 (绿色)
    for m in re.finditer(r"'[^']*'", sql):
        text_widget.tag_add('sql_str', f'1.0+{m.start()}c', f'1.0+{m.end()}c')

    # 数字 (橙色)
    for m in re.finditer(r'\b(\d+\.?\d*)\b', sql):
        text_widget.tag_add('sql_num', f'1.0+{m.start()}c', f'1.0+{m.end()}c')

    # 注释 (灰色)
    for m in re.finditer(r'--[^\n]*', sql):
        text_widget.tag_add('sql_cmt', f'1.0+{m.start()}c', f'1.0+{m.end()}c')

    # 关键字 (蓝色)
    for kw in SQL_KW:
        for m in re.finditer(r'\b' + kw.replace(' ', r'\s+') + r'\b', sql, re.IGNORECASE):
            text_widget.tag_add('sql_kw', f'1.0+{m.start()}c', f'1.0+{m.end()}c')

    text_widget.config(state='disabled')

# ═══════════════════════════════════════════
# 主应用类
# ═══════════════════════════════════════════
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('SQLAgent Desktop')
        self.root.geometry('1200x780')
        self.root.minsize(900, 600)
        self.root.configure(bg=BG)

        self._setup_style()
        self._build_ui()
        self._load_data()

    # ── 样式 ────────────────────────────────
    def _setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')

        # 全局默认
        style.configure('.', background=BG, foreground=WHITE, font=FONT_SM,
                        fieldbackground=INPUT_BG, borderwidth=0, relief='flat')
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=WHITE)
        style.configure('TButton', background=INPUT_BG, foreground=WHITE,
                        borderwidth=1, padding=(8, 4), relief='flat')
        style.map('TButton', background=[('active', ACCENT), ('disabled', MUTED)],
                  foreground=[('disabled', GRAY)])
        style.configure('Accent.TButton', background=ACCENT, foreground=WHITE)
        style.configure('Danger.TButton', background=DANGER, foreground=WHITE)
        style.configure('TEntry', fieldbackground=INPUT_BG, foreground=WHITE)
        style.configure('TCombobox', fieldbackground=INPUT_BG, foreground=WHITE,
                        arrowcolor=WHITE, selectbackground=INPUT_BG)
        style.map('TCombobox', fieldbackground=[('readonly', INPUT_BG)],
                  selectbackground=[('readonly', INPUT_BG)])
        style.configure('TPanedwindow', background=BG)
        style.configure('TNotebook', background=BG, borderwidth=0)
        style.configure('TNotebook.Tab', background=PANEL, foreground=WHITE,
                        padding=(12, 4), borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', ACCENT)])
        style.configure('Treeview', background=PANEL, foreground=WHITE,
                        fieldbackground=PANEL, borderwidth=0, rowheight=24)
        style.configure('Treeview.Heading', background=INPUT_BG, foreground=WHITE,
                        font=('Consolas', 9, 'bold'), borderwidth=0, padding=(4, 2))
        style.map('Treeview', background=[('selected', ACCENT)])
        style.configure('Vertical.TScrollbar', background=INPUT_BG, troughcolor=BG,
                        arrowcolor=GRAY, borderwidth=0)
        style.configure('Horizontal.TScrollbar', background=INPUT_BG, troughcolor=BG,
                        arrowcolor=GRAY, borderwidth=0)
        style.configure('Small.TCheckbutton', background=BG, foreground=WHITE,
                        font=FONT_SM, padding=(2, 0))
        # Combobox 下拉列表
        self.root.option_add('*TCombobox*Listbox.background', PANEL)
        self.root.option_add('*TCombobox*Listbox.foreground', WHITE)
        self.root.option_add('*TCombobox*Listbox.selectBackground', ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', WHITE)

    # ── 构建 UI ─────────────────────────────
    def _build_ui(self):
        # 主 PanedWindow (左右分栏)
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill='both', expand=True, padx=(0, 0))

        self.left_frame = ttk.Frame(self.paned)
        self.right_frame = ttk.Frame(self.paned)
        self.paned.add(self.left_frame, weight=42)
        self.paned.add(self.right_frame, weight=58)

        self._build_left()
        self._build_right()
        self._build_statusbar()

    def _build_left(self):
        lf = self.left_frame

        # ── DB 配置栏 ──
        db_bar = ttk.Frame(lf)
        db_bar.pack(fill='x', padx=6, pady=(6, 0))

        self.db_combo = ttk.Combobox(db_bar, state='readonly')
        self.db_combo.pack(side='left', fill='x', expand=True)
        self.db_combo.bind('<<ComboboxSelected>>', self._on_db_select)

        ttk.Button(db_bar, text='+', width=3, command=self._add_db_dialog).pack(side='left', padx=(4, 0))
        ttk.Button(db_bar, text='测', width=3, command=self._test_db).pack(side='left', padx=(4, 0))
        self.db_status = ttk.Label(db_bar, text='')
        self.db_status.pack(side='right', padx=(8, 0))

        # ── 自然语言输入 ──
        nl_label = ttk.Label(lf, text='自然语言输入', font=('Consolas', 9, 'bold'), foreground=GRAY)
        nl_label.pack(anchor='w', padx=8, pady=(8, 2))

        self.input_text = tk.Text(lf, height=6, bg=INPUT_BG, fg=WHITE, font=FONT,
                                  insertbackground=WHITE, relief='flat',
                                  padx=8, pady=6, wrap='word', undo=True)
        self.input_text.pack(fill='x', padx=6)
        self.input_text.insert('1.0', '')
        self.input_text.bind('<Control-Return>', lambda e: self._generate_sql())

        # 输入区滚动条
        # 按钮行
        btn_row = ttk.Frame(lf)
        btn_row.pack(fill='x', padx=6, pady=(4, 0))
        self.gen_btn = ttk.Button(btn_row, text='生成 SQL', style='Accent.TButton',
                                  command=self._generate_sql)
        self.gen_btn.pack(side='left')
        ttk.Button(btn_row, text='清空', command=self._clear_input).pack(side='left', padx=(6, 0))

        # ── SQL 预览 ──
        sql_label = ttk.Label(lf, text='SQL 预览', font=('Consolas', 9, 'bold'), foreground=GRAY)
        sql_label.pack(anchor='w', padx=8, pady=(10, 2))

        # SQL 预览框 (带滚动条)
        sql_frame = ttk.Frame(lf)
        sql_frame.pack(fill='both', expand=True, padx=6)

        self.sql_text = tk.Text(sql_frame, bg=BG, fg=WHITE, font=FONT,
                                insertbackground=WHITE, relief='flat',
                                padx=8, pady=6, wrap='none', undo=True)
        sql_scroll_y = ttk.Scrollbar(sql_frame, orient='vertical', command=self.sql_text.yview)
        sql_scroll_x = ttk.Scrollbar(sql_frame, orient='horizontal', command=self.sql_text.xview)
        self.sql_text.configure(yscrollcommand=sql_scroll_y.set, xscrollcommand=sql_scroll_x.set)

        self.sql_text.grid(row=0, column=0, sticky='nsew')
        sql_scroll_y.grid(row=0, column=1, sticky='ns')
        sql_scroll_x.grid(row=1, column=0, sticky='ew')
        sql_frame.grid_rowconfigure(0, weight=1)
        sql_frame.grid_columnconfigure(0, weight=1)

        self.sql_text.insert('1.0', '-- AI 生成的 SQL 将显示在这里')
        self.sql_text.config(state='disabled')

        # 配置 tag 颜色
        for tag, color in [('sql_kw', '#6CB6FF'), ('sql_str', '#96D0A0'),
                           ('sql_num', '#F0B679'), ('sql_cmt', GRAY)]:
            self.sql_text.tag_configure(tag, foreground=color)
        self.sql_text.tag_configure('sql_kw', foreground='#6CB6FF', font=('Consolas', 10, 'bold'))

        # ── 执行按钮行 ──
        exec_row = ttk.Frame(lf)
        exec_row.pack(fill='x', padx=6, pady=(6, 8))
        self.exec_btn = ttk.Button(exec_row, text='执行 SQL', style='Accent.TButton',
                                   command=self._execute_sql)
        self.exec_btn.pack(side='left')
        ttk.Button(exec_row, text='导出 CSV', command=self._export_csv).pack(side='left', padx=(6, 0))
        self.tx_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(exec_row, text='开启事务', variable=self.tx_var,
                        style='Small.TCheckbutton').pack(side='left', padx=(12, 0))
        self.copy_btn = ttk.Button(exec_row, text='复制 SQL', command=self._copy_sql)
        self.copy_btn.pack(side='right')

    def _build_right(self):
        rf = self.right_frame

        # ── 执行状态栏 ──
        self.result_bar = ttk.Frame(rf)
        self.result_bar.pack(fill='x', padx=6, pady=(6, 0))

        self.rb_type = ttk.Label(self.result_bar, text='类型: —')
        self.rb_type.pack(side='left', padx=(0, 16))
        self.rb_time = ttk.Label(self.result_bar, text='耗时: —')
        self.rb_time.pack(side='left', padx=(0, 16))
        self.rb_rows = ttk.Label(self.result_bar, text='行数: —')
        self.rb_rows.pack(side='left')
        self.rb_status = ttk.Label(self.result_bar, text='')
        self.rb_status.pack(side='right')

        # ── Notebook (Tabs) ──
        self.notebook = ttk.Notebook(rf)
        self.notebook.pack(fill='both', expand=True, padx=6, pady=(4, 0))

        # Tab 1: 查询结果表格
        self.tab_result = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_result, text='查询结果')

        # Treeview + 滚动条
        tree_frame = ttk.Frame(self.tab_result)
        tree_frame.pack(fill='both', expand=True)

        self.tree = ttk.Treeview(tree_frame, show='headings')
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll_y.grid(row=0, column=1, sticky='ns')
        tree_scroll_x.grid(row=1, column=0, sticky='ew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # 翻页按钮
        page_frame = ttk.Frame(self.tab_result)
        page_frame.pack(fill='x', pady=4)
        self.page_label = ttk.Label(page_frame, text='')
        self.page_label.pack(side='left', padx=6)
        ttk.Button(page_frame, text='← 上一页', command=self._prev_page).pack(side='left', padx=(6, 2))
        ttk.Button(page_frame, text='下一页 →', command=self._next_page).pack(side='left', padx=2)

        # Tab 2: 执行日志
        self.tab_log = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_log, text='执行日志')
        self.log_text = scrolledtext.ScrolledText(self.tab_log, bg=BG, fg=WHITE, font=FONT,
                                                   relief='flat', padx=8, pady=6, wrap='word')
        self.log_text.pack(fill='both', expand=True)
        self.log_text.config(state='disabled')

        # Tab 3: 历史记录
        self.tab_history = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_history, text='历史记录')

        hist_top = ttk.Frame(self.tab_history)
        hist_top.pack(fill='x', padx=4, pady=4)
        ttk.Button(hist_top, text='清除历史', command=self._clear_history).pack(side='right')

        self.history_list = tk.Listbox(self.tab_history, bg=PANEL, fg=WHITE, font=FONT_SM,
                                       selectbackground=ACCENT, selectforeground=WHITE,
                                       relief='flat', borderwidth=0, activestyle='none')
        hist_scroll = ttk.Scrollbar(self.tab_history, orient='vertical', command=self.history_list.yview)
        self.history_list.configure(yscrollcommand=hist_scroll.set)
        self.history_list.pack(side='left', fill='both', expand=True)
        hist_scroll.pack(side='right', fill='y')
        self.history_list.bind('<Double-Button-1>', self._on_history_click)

        # 空状态
        self._show_empty()

    def _build_statusbar(self):
        self.statusbar = ttk.Frame(self.root)
        self.statusbar.pack(fill='x', side='bottom')

        self.sb_db = ttk.Label(self.statusbar, text='● 检测中...')
        self.sb_db.pack(side='left', padx=8)
        self.sb_history = ttk.Label(self.statusbar, text='')
        self.sb_history.pack(side='right', padx=8)

    # ── 数据加载 ────────────────────────────
    def _load_data(self):
        load_db_configs()
        self._refresh_db_combo()
        self._refresh_history()
        self._check_health()
        # 定时健康检查
        self.root.after(15000, self._periodic_health)

    def _periodic_health(self):
        self._check_health()
        self.root.after(15000, self._periodic_health)

    # ── DB 配置 ─────────────────────────────
    def _refresh_db_combo(self):
        names = [f"{c.get('name','')} ({c.get('type','mysql')})" for c in DB_CONFIGS]
        self.db_combo['values'] = names
        if DB_CONFIGS:
            self.db_combo.current(0)
            global CURRENT_DB
            CURRENT_DB = DB_CONFIGS[0]

    def _on_db_select(self, _e=None):
        idx = self.db_combo.current()
        if 0 <= idx < len(DB_CONFIGS):
            global CURRENT_DB
            CURRENT_DB = DB_CONFIGS[idx]

    def _add_db_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title('新增数据库连接')
        dialog.geometry('420x380')
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()

        fields = [
            ('名称', 'name', ''),
            ('类型', 'type', 'mysql'),
            ('地址', 'host', 'localhost'),
            ('端口', 'port', '3306'),
            ('用户名', 'user', 'root'),
            ('密码', 'password', ''),
            ('数据库', 'database', 'sqlagent'),
        ]
        entries = {}
        for i, (label, key, default) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=12, pady=6, sticky='e')
            if key == 'password':
                e = ttk.Entry(dialog, show='*', width=30)
            else:
                e = ttk.Entry(dialog, width=30)
            e.insert(0, default)
            e.grid(row=i, column=1, padx=12, pady=6, sticky='w')
            entries[key] = e

        def save():
            cfg = {k: e.get() for k, e in entries.items()}
            cfg['port'] = int(cfg['port']) if cfg['port'].isdigit() else 3306
            cfg['id'] = datetime.now().strftime('%Y%m%d%H%M%S')
            if not cfg['name']:
                messagebox.showwarning('提示', '请输入连接名称')
                return
            DB_CONFIGS.append(cfg)
            save_db_configs()
            self._refresh_db_combo()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=16)
        ttk.Button(btn_frame, text='取消', command=dialog.destroy).pack(side='left', padx=4)
        ttk.Button(btn_frame, text='保存', style='Accent.TButton', command=save).pack(side='left', padx=4)

    def _test_db(self):
        if not CURRENT_DB:
            messagebox.showwarning('提示', '请先选择数据库连接')
            return
        self.db_status.config(text='检测中...', foreground=WARNING)

        def do_test():
            try:
                r = requests.post(f'{API_BASE}/api/execute',
                                  json={'sql': 'SELECT 1', 'read_only': True}, timeout=5)
                return r.json().get('success', False)
            except Exception:
                return False

        def callback(ok):
            if ok:
                self.db_status.config(text='✓ 连接成功', foreground=SUCCESS)
            else:
                self.db_status.config(text='✗ 连接失败', foreground=DANGER)

        run_async(do_test, callback)

    # ── 生成 SQL ────────────────────────────
    def _generate_sql(self):
        question = self.input_text.get('1.0', 'end-1c').strip()
        if not question:
            messagebox.showwarning('提示', '请输入问题')
            return

        self.gen_btn.config(text='生成中...', state='disabled')

        def do_generate():
            try:
                r = requests.post(f'{API_BASE}/api/query',
                                  json={'question': question}, timeout=120)
                return r.json()
            except Exception as e:
                return {'error': str(e)}

        def callback(resp):
            self.gen_btn.config(text='生成 SQL', state='normal')
            sql = resp.get('sql', '')
            if resp.get('error'):
                sql = f"-- 生成失败: {resp['error']}"
            elif not sql:
                sql = resp.get('answer', '-- 未生成 SQL')

            highlight_sql(self.sql_text, sql)
            self._log(f"[生成SQL] {question}\n{sql}\n")

        run_async(do_generate, callback)

    # ── 执行 SQL ────────────────────────────
    def _execute_sql(self):
        sql = self.sql_text.get('1.0', 'end-1c').strip()
        if not sql or sql.startswith('--'):
            return

        # 高危拦截
        upper = sql.upper()
        for kw in DANGER_KW:
            if kw.upper() in upper:
                if kw == 'DELETE FROM' and 'WHERE' in upper:
                    continue  # 有 WHERE 就放行
                if not messagebox.askyesno('⚠️ 高危操作',
                                           f'检测到高危语句: {kw}\n\n该操作不可逆，确认执行？'):
                    return

        self.exec_btn.config(text='执行中...', state='disabled')
        start = datetime.now()

        def do_execute():
            try:
                is_write = bool(re.match(r'^\s*(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)', sql, re.I))
                r = requests.post(f'{API_BASE}/api/execute',
                                  json={'sql': sql, 'read_only': not is_write}, timeout=30)
                data = r.json()
                data['_elapsed'] = (datetime.now() - start).total_seconds() * 1000
                data['_is_write'] = is_write
                return data
            except Exception as e:
                return {'error': str(e), 'success': False,
                        '_elapsed': (datetime.now() - start).total_seconds() * 1000}

        def callback(resp):
            self.exec_btn.config(text='执行 SQL', state='normal')
            elapsed = resp.get('_elapsed', 0)
            is_write = resp.get('_is_write', False)

            # 更新状态栏
            sql_type = 'SELECT'
            if is_write:
                sql_type = sql.strip().split()[0].upper()
            self.rb_type.config(text=f'类型: {sql_type}')
            self.rb_time.config(text=f'耗时: {elapsed:.0f}ms')

            if resp.get('success'):
                data = resp.get('data')
                if data and data.get('columns'):
                    self.rb_rows.config(text=f'行数: {data["row_count"]}')
                    self.rb_status.config(text='✓ 执行成功', foreground=SUCCESS)
                    self._show_table(data)
                    self.notebook.select(self.tab_result)
                else:
                    self.rb_rows.config(text=f'行数: {resp.get("affectedRows", data.get("row_count", 0))}')
                    self.rb_status.config(text='✓ 执行成功', foreground=SUCCESS)
                    self._show_log(f'✓ 执行成功\n受影响行数: {resp.get("affectedRows", 0)}\n耗时: {elapsed:.0f}ms')
                    self.notebook.select(self.tab_log)
            else:
                self.rb_rows.config(text='行数: —')
                self.rb_status.config(text='✗ 执行失败', foreground=DANGER)
                error = resp.get('error', '未知错误')
                self._show_log(f'✗ 执行失败\n{error}\n耗时: {elapsed:.0f}ms')
                self.notebook.select(self.tab_log)

            # 保存历史
            history = load_history()
            history.append({
                'sql': sql, 'success': resp.get('success', False),
                'elapsed': f'{elapsed:.0f}ms',
                'time': datetime.now().strftime('%m/%d %H:%M'),
            })
            save_history(history)
            self._refresh_history()

        run_async(do_execute, callback)

    # ── 结果表格 ────────────────────────────
    _rows = []
    _page = 0
    PAGE_SIZE = 100

    def _show_table(self, data):
        self._rows = data['rows']
        self._page = 0
        columns = data['columns']
        # 清空旧列
        self.tree['columns'] = columns
        self.tree['show'] = 'headings'
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, minwidth=80)
        self._render_page()

    def _render_page(self):
        self.tree.delete(*self.tree.get_children())
        start = self._page * self.PAGE_SIZE
        page_rows = self._rows[start:start + self.PAGE_SIZE]
        for row in page_rows:
            self.tree.insert('', 'end', values=[str(v) if v is not None else 'NULL' for v in row])
        total = len(self._rows)
        pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page_label.config(text=f'第 {self._page + 1}/{pages} 页 · 共 {total} 行')

    def _prev_page(self):
        if self._page > 0:
            self._page -= 1
            self._render_page()

    def _next_page(self):
        total = len(self._rows)
        pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self._page < pages - 1:
            self._page += 1
            self._render_page()

    # ── 日志 ────────────────────────────────
    def _log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert('end', f'{msg}\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def _show_log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.insert('1.0', msg)
        self.log_text.config(state='disabled')

    # ── 历史记录 ────────────────────────────
    def _refresh_history(self):
        self.history_list.delete(0, 'end')
        history = load_history()
        for h in reversed(history[-50:]):
            status = '✓' if h.get('success') else '✗'
            label = f"{status} {h.get('time','')} | {h.get('elapsed','')} | {h.get('sql','')[:60]}"
            self.history_list.insert('end', label)
        self.sb_history.config(text=f'历史: {len(history)} 条')

    def _on_history_click(self, _e):
        sel = self.history_list.curselection()
        if not sel:
            return
        history = load_history()
        idx = len(history) - 1 - sel[0]
        if 0 <= idx < len(history):
            sql = history[idx].get('sql', '')
            highlight_sql(self.sql_text, sql)

    def _clear_history(self):
        if messagebox.askyesno('确认', '确定清除所有历史记录？'):
            save_history([])
            self._refresh_history()

    # ── 空状态 ──────────────────────────────
    def _show_empty(self):
        # 在日志 tab 显示引导
        self._show_log('在左侧输入问题，点击「生成 SQL」，然后「执行 SQL」\n查询结果将显示在这里')

    # ── 其他操作 ────────────────────────────
    def _clear_input(self):
        self.input_text.delete('1.0', 'end')

    def _copy_sql(self):
        sql = self.sql_text.get('1.0', 'end-1c').strip()
        if sql and not sql.startswith('-- AI'):
            self.root.clipboard_clear()
            self.root.clipboard_append(sql)
            messagebox.showinfo('提示', 'SQL 已复制到剪贴板')

    def _export_csv(self):
        if not self._rows:
            messagebox.showwarning('提示', '没有可导出的数据')
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension='.csv',
                                            filetypes=[('CSV', '*.csv')])
        if not path:
            return
        import csv
        cols = list(self.tree['columns'])
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(self._rows)
        messagebox.showinfo('提示', f'已导出到 {path}')

    def _check_health(self):
        def do_check():
            try:
                r = requests.get(f'{API_BASE}/health', timeout=3)
                return r.json()
            except Exception:
                return None

        def callback(resp):
            if resp and resp.get('database'):
                self.sb_db.config(text='● MySQL 已连接', foreground=SUCCESS)
            elif resp:
                self.sb_db.config(text='● MySQL 断开', foreground=WARNING)
            else:
                self.sb_db.config(text='● API 离线', foreground=DANGER)

        run_async(do_check, callback)

    # ── 运行 ────────────────────────────────
    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════
app = App()

if __name__ == '__main__':
    app.run()
