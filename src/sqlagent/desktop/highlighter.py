"""
SQL 语法高亮器
"""
from typing import List

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

from .constants import MUTED

SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
    'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON', 'AS', 'GROUP', 'BY',
    'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'INSERT', 'INTO',
    'VALUES', 'UPDATE', 'SET', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TABLE',
    'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'EXPLAIN', 'INDEX',
    'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'NULL', 'DEFAULT',
    'AUTO_INCREMENT', 'CASCADE', 'INFORMATION_SCHEMA', 'TABLE_NAME',
    'COLUMN_NAME', 'DATE_SUB', 'DATE_ADD', 'NOW', 'VARCHAR', 'INT',
    'BIGINT', 'DECIMAL', 'TEXT', 'DATETIME', 'TIMESTAMP', 'IF', 'EXISTS',
    'SHOW', 'DESCRIBE', 'USE', 'TRUNCATE', 'RENAME', 'REPLACE', 'MERGE',
    'ASC', 'DESC', 'IS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'ALL',
    'ANY', 'SOME', 'FULL', 'CROSS', 'NATURAL', 'USING', 'UNIQUE', 'CHECK',
    'CONSTRAINT', 'ADD', 'COLUMN', 'MODIFY', 'CHANGE', 'RENAME', 'TO',
    'GRANT', 'REVOKE', 'ON', 'SCHEMA', 'DATABASE', 'VIEW', 'PROCEDURE',
    'FUNCTION', 'TRIGGER', 'EVENT', 'CHARACTER', 'COLLATE', 'ENGINE',
    'INNODB', 'MYISAM', 'CHARSET', 'UTF8MB4',
]


class SqlHighlighter(QSyntaxHighlighter):
    """SQL 语法高亮器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules: List[tuple] = []

        # 关键字 (Darcula橙)
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor('#CC7832'))
        kw_fmt.setFontWeight(QFont.Bold)
        for kw in SQL_KEYWORDS:
            pattern = QRegularExpression(
                r'\b' + kw.replace(' ', r'\s+') + r'\b',
                QRegularExpression.CaseInsensitiveOption
            )
            self.rules.append((pattern, kw_fmt))

        # 字符串 (Darcula绿)
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor('#6A8759'))
        self.rules.append((QRegularExpression(r"'[^']*'"), str_fmt))
        self.rules.append((QRegularExpression(r'"[^"]*"'), str_fmt))

        # 数字 (Darcula蓝)
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor('#6897BB'))
        self.rules.append((QRegularExpression(r'\b\d+\.?\d*\b'), num_fmt))

        # 注释 (灰色斜体)
        cmt_fmt = QTextCharFormat()
        cmt_fmt.setForeground(QColor(MUTED))
        cmt_fmt.setFontItalic(True)
        self.rules.append((QRegularExpression(r'--[^\n]*'), cmt_fmt))
        self.rules.append((QRegularExpression(r'/\*.*?\*/',
                           QRegularExpression.DotMatchesEverythingOption), cmt_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)
