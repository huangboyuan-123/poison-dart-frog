"""
Redis 路由 — 键浏览、值读写、键删除。
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/redis", tags=["redis"])

# Redis 连接 (延迟导入)
_redis_client = None


def _get_redis_module():
    try:
        import redis as _redis
        return _redis
    except ImportError:
        raise HTTPException(status_code=500, detail="redis-py 未安装，请执行 pip install redis")


def get_redis():
    global _redis_client
    if _redis_client is None:
        r = _get_redis_module()
        _redis_client = r.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", "") or None,
            decode_responses=True,
        )
    return _redis_client


class SetValueRequest(BaseModel):
    value: str


@router.get("/keys")
async def list_keys(pattern: str = Query("*")):
    """列出匹配模式的 Redis 键"""
    try:
        r = get_redis()
        keys = []
        types = {}
        cursor = 0
        count = 0
        while True:
            cursor, batch = r.scan(cursor, match=pattern, count=100)
            for k in batch:
                keys.append(k)
                try:
                    t = r.type(k)
                    # 按类型着色
                    color_map = {
                        'string': '#96D0A0', 'hash': '#F0B679',
                        'list': '#6CB6FF', 'set': '#E05555',
                        'zset': '#D29922', 'stream': '#8B5CF6',
                    }
                    types[k] = color_map.get(t, '#86909C')
                except Exception:
                    types[k] = '#86909C'
            count += len(batch)
            if cursor == 0 or count >= 500:
                break
        return {"keys": keys, "types": types, "total": len(keys)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/key/{key:path}")
async def get_key(key: str):
    """获取键的值和类型"""
    try:
        r = get_redis()
        t = r.type(key)
        if t == 'none':
            raise HTTPException(status_code=404, detail=f"键 '{key}' 不存在")

        if t == 'string':
            value = r.get(key)
        elif t == 'hash':
            value = r.hgetall(key)
        elif t == 'list':
            value = r.lrange(key, 0, -1)
        elif t == 'set':
            value = list(r.smembers(key))
        elif t == 'zset':
            value = r.zrange(key, 0, -1, withscores=True)
        else:
            value = str(r.execute_command('DUMP', key))

        return {"key": key, "type": t, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/key/{key:path}")
async def set_key(key: str, req: SetValueRequest):
    """设置字符串键的值"""
    try:
        r = get_redis()
        r.set(key, req.value)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/key/{key:path}")
async def delete_key(key: str):
    """删除键"""
    try:
        r = get_redis()
        r.delete(key)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RedisQueryRequest(BaseModel):
    question: str


class RedisExecuteRequest(BaseModel):
    command: str


@router.post("/query")
async def redis_query(req: RedisQueryRequest):
    """AI 自然语言 → Redis 命令"""
    try:
        import os as _os
        import re as _re
        api_key = _os.getenv("DEEPSEEK_API_KEY") or _os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return {"error": "未配置 LLM API Key", "command": "", "answer": ""}

        # 提取问题中提到的 key 并查询其类型
        key_context = ""
        try:
            r = get_redis()
            # 简单提取可能的 key 名称
            key_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_:]*)\b'
            potential_keys = _re.findall(key_pattern, req.question)
            for k in potential_keys[:3]:  # 最多查3个
                t = r.type(k)
                if t != 'none':
                    if t == 'string':
                        val = r.get(k)
                        key_context += f"\n键 '{k}': 类型={t}, 值={val}"
                    elif t == 'hash':
                        val = r.hgetall(k)
                        key_context += f"\n键 '{k}': 类型=hash, 字段={val}"
        except Exception:
            pass

        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate

        llm = ChatOpenAI(
            model=_os.getenv("LLM_MODEL", "deepseek-chat"),
            api_key=api_key,
            base_url=_os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            temperature=0,
        )

        human_msg = req.question
        if key_context:
            human_msg = f"当前 Redis 状态:{key_context}\n\n用户问题: {req.question}"

        prompt = ChatPromptTemplate.from_messages([(
            "system",
            "你是 Redis 专家。用户用中文描述需求，你输出对应的 Redis 命令。"
            "只输出命令，每行一个，不要解释。\n\n"
            "重要规则:\n"
            "- Hash 用 HSET/HGET/HGETALL/HDEL\n"
            "- String 用 SET/GET\n"
            "- 改键类型: DEL旧键 → 用新类型命令重建 (如转Hash: DEL key + HSET key f1 v1 f2 v2)\n"
            "- 根据提供的键类型信息选择正确的命令\n"
            "- TYPE 只查看不修改，不要单独输出 TYPE\n"
        ), ("human", "{question}")])

        chain = prompt | llm
        response = chain.invoke({"question": human_msg})
        return {"command": response.content, "answer": response.content}
    except Exception as e:
        return {"error": str(e), "command": "", "answer": ""}


@router.post("/execute")
async def redis_execute(req: RedisExecuteRequest):
    """执行 Redis 命令（带类型检查）"""
    try:
        r = get_redis()
        results = []
        for line in req.command.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            cmd = parts[0].upper()
            args = parts[1:]

            # 类型敏感命令：先检查 key 类型
            type_sensitive = {'HGET', 'HSET', 'HGETALL', 'HDEL', 'LPUSH', 'RPUSH',
                              'LRANGE', 'SADD', 'SMEMBERS', 'ZADD', 'ZRANGE'}
            if cmd in type_sensitive and args:
                key = args[0]
                t = r.type(key)
                expected = {'HGET': 'hash', 'HSET': 'hash', 'HGETALL': 'hash', 'HDEL': 'hash',
                            'LPUSH': 'list', 'RPUSH': 'list', 'LRANGE': 'list',
                            'SADD': 'set', 'SMEMBERS': 'set',
                            'ZADD': 'zset', 'ZRANGE': 'zset'}.get(cmd)
                if expected and t != expected and t != 'none':
                    results.append(f'{cmd}: 类型错误 — {key} 是 {t} 类型, 但 {cmd} 需要 {expected}')
                    continue

            try:
                result = r.execute_command(cmd, *args)
                results.append(f'{cmd}: {result}')
            except Exception as e:
                results.append(f'{cmd}: ERROR - {e}')
        return {"ok": True, "result": '\n'.join(results)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
