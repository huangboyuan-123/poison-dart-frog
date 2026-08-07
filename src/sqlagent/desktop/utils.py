"""
工具函数: Markdown 转换、SQL/Redis 命令提取
"""
import re


def _md_to_html(text: str) -> str:
    """简单 Markdown → HTML 转换，保留换行和段落"""
    import html
    text = html.escape(text, quote=False)

    # 代码块 ```...``` — 先处理，保留内部换行
    def _code_block(m):
        code = m.group(2).strip()
        return f'<pre style="background:#1E1E1E;padding:8px 12px;border-radius:4px;margin:8px 0;"><code style="color:#6CB6FF;">{code}</code></pre>'
    text = re.sub(r'```(\w*)\n(.*?)```', _code_block, text, flags=re.DOTALL)

    # 行内代码 `...`
    text = re.sub(r'`([^`]+)`', r'<code style="background:#3C3F41;padding:1px 5px;border-radius:3px;">\1</code>', text)

    # 标题
    text = re.sub(r'^### (.+)$', r'<h4 style="margin:8px 0 4px;color:#E8E8E8;">\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h3 style="margin:10px 0 6px;color:#E8E8E8;">\1</h3>', text, flags=re.MULTILINE)
    # 加粗和斜体
    text = re.sub(r'\*\*(.+?)\*\*', r'<b style="color:#FFC66D;">\1</b>', text)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    # 无序列表
    text = re.sub(r'^- (.+)$', r'<li style="margin:2px 0;">\1</li>', text, flags=re.MULTILINE)
    # 分隔线
    text = re.sub(r'^---$', r'<hr style="border:0;border-top:1px solid rgba(255,255,255,0.1);margin:8px 0;">', text, flags=re.MULTILINE)

    # 连续换行 → </p><p>
    text = re.sub(r'\n\n+', '</p><p style="margin:6px 0;">', text)
    # 单换行 → <br>
    text = text.replace('\n', '<br>')
    return f'<div style="color:#A9B7C6;line-height:1.7;font-size:13px;"><p style="margin:6px 0;">{text}</p></div>'


def _extract_redis_commands(text: str) -> list:
    """截取 correct-command 标识符后面的所有内容"""
    marker = '$correct-command$'
    idx = text.find(marker)
    if idx < 0:
        return []
    after = text[idx + len(marker):].strip()
    return [line.strip() for line in after.split(chr(10)) if line.strip()]


def _extract_sql_from_stream(text: str) -> str:
    """从流式文本中提取 SQL 语句并修复格式"""
    # 匹配 ```sql ... ``` 代码块
    m = re.search(r'```sql\s*(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if m:
        sql = m.group(1).strip()
    else:
        # 匹配 SQL 语句
        m = re.search(r'(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|SHOW|DESCRIBE|EXPLAIN)\b.*?;', text, re.DOTALL | re.IGNORECASE)
        if m:
            sql = m.group(0).strip()
        else:
            return ''
    # 修复常见空格问题
    sql = re.sub(r'\*FROM', '* FROM', sql)
    sql = re.sub(r'(\w)JOIN', r'\1 JOIN', sql)
    sql = re.sub(r'(\w)WHERE', r'\1 WHERE', sql)
    sql = re.sub(r'(\w)FROM', r'\1 FROM', sql)
    sql = re.sub(r'(\w)LIMIT', r'\1 LIMIT', sql)
    sql = re.sub(r'(\w)ORDER', r'\1 ORDER', sql)
    sql = re.sub(r'(\w)GROUP', r'\1 GROUP', sql)
    sql = re.sub(r'(\w)ON\b', r'\1 ON', sql)
    return sql
