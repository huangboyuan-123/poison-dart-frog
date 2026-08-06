"""
Redis 路由 — 键浏览、值读写、键删除、AI对话。
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/redis", tags=["redis"])

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
    try:
        r = get_redis()
        keys, types_data = [], {}
        cursor = 0
        while True:
            cursor, batch = r.scan(cursor, match=pattern, count=100)
            for k in batch:
                keys.append(k)
                try:
                    t = r.type(k)
                    color_map = {'string': '#96D0A0', 'hash': '#F0B679', 'list': '#6CB6FF',
                                 'set': '#E05555', 'zset': '#D29922', 'stream': '#8B5CF6'}
                    types_data[k] = color_map.get(t, '#86909C')
                except Exception:
                    types_data[k] = '#86909C'
            if cursor == 0 or len(keys) >= 500:
                break
        return {"keys": keys, "types": types_data, "total": len(keys)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/key/{key:path}")
async def get_key(key: str):
    try:
        r = get_redis()
        t = r.type(key)
        if t == 'none':
            raise HTTPException(status_code=404, detail=f"键 '{key}' 不存在")
        if t == 'string': value = r.get(key)
        elif t == 'hash': value = r.hgetall(key)
        elif t == 'list': value = r.lrange(key, 0, -1)
        elif t == 'set': value = list(r.smembers(key))
        elif t == 'zset': value = r.zrange(key, 0, -1, withscores=True)
        else: value = str(r.execute_command('DUMP', key))
        return {"key": key, "type": t, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/key/{key:path}")
async def set_key(key: str, req: SetValueRequest):
    try:
        r = get_redis()
        r.set(key, req.value)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/key/{key:path}")
async def delete_key(key: str):
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


@router.post("/query/stream")
async def redis_query_stream(req: RedisQueryRequest):
    """Redis AI 流式 — SSE 推送思考过程"""
    import asyncio
    from fastapi.responses import StreamingResponse

    async def event_stream():
        # 调用非流式 query 获取结果
        result = await redis_query(req)
        text = result.get('command', result.get('answer', result.get('error', '')))
        if not text:
            yield f"data: [ERROR] 未生成命令\n\n"
            return
        for char in text:
            yield f"data: {char}\n\n"
            await asyncio.sleep(0.015)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/query")
async def redis_query(req: RedisQueryRequest):
    """AI 自然语言 → Redis 命令（带当前数据上下文）"""
    try:
        api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            return {"error": "未配置 LLM API Key", "command": "", "answer": ""}

        # 提取问题中的关键词 + 扫描全量键结构
        import re as _re
        r = get_redis()
        data_context = ""

        # 1. 扫描现有键总览 (最多50个)
        try:
            cursor, all_keys = 0, []
            while True:
                cursor, batch = r.scan(cursor, count=50)
                all_keys.extend(batch)
                if cursor == 0 or len(all_keys) >= 100:
                    break
            if all_keys:
                data_context += f"现有 {len(all_keys)} 个键: {', '.join(sorted(all_keys)[:30])}"
        except Exception:
            pass

        # 2. 查找问题中提到的具体键
        key_pattern = _re.compile(r'\b([a-zA-Z_][a-zA-Z0-9_:]*)\b')
        seen = set()
        for m in key_pattern.finditer(req.question):
            k = m.group(1)
            if k in seen or len(k) < 2:
                continue
            seen.add(k)
            try:
                t = r.type(k)
                if t == 'string':
                    data_context += f"\n  {k} (string) = {r.get(k)}"
                elif t == 'hash':
                    data_context += f"\n  {k} (hash) = {r.hgetall(k)}"
                elif t == 'list':
                    data_context += f"\n  {k} (list) = {r.lrange(k, 0, -1)}"
                elif t == 'set':
                    data_context += f"\n  {k} (set) = {list(r.smembers(k))}"
            except Exception:
                pass

        # 3. 模糊匹配: 在键名中搜索问题关键词
        for word in _re.findall(r'[\w]+', req.question):
            if len(word) >= 2 and word.lower() not in ('的', '给', '把', '在', '和', '是', '请', '帮', '我', '查', '看', '删', '修改', '添加', '创建', 'the', 'a', 'an'):
                try:
                    matched = [k for k in all_keys if word.lower() in k.lower()]
                    for k in matched[:5]:
                        if k not in seen:
                            seen.add(k)
                            t = r.type(k)
                            if t == 'string':
                                data_context += f"\n  {k} (string) = {r.get(k)}"
                            elif t == 'hash':
                                data_context += f"\n  {k} (hash) = {r.hgetall(k)}"
                except Exception:
                    pass

        human_msg = (
            f"【Redis 真实数据】{data_context}\n\n"
            f"【用户需求】{req.question}\n\n"
            f"输出格式(铁律):\n"
            f"先分析。然后单独一行写 $correct-command$\n"
            f"之后每条Redis命令独占一行，用回车换行分隔。\n"
            f"示例输出:\n"
            f"$correct-command$\n"
            f"HGETALL user:1\n"
            f"HGETALL user:2\n\n"
            f"禁止: HGETALL user:1HGETALL user:2 (多条合在一行)"
        )

        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate

        llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            api_key=api_key,
            base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            temperature=0,
        )

        prompt = ChatPromptTemplate.from_messages([(
            "system",
            "你是 Redis 专家。请根据【真实数据】分析并生成 Redis 命令。\n\n"
            "输出格式（直接输出，不要代码块）：\n"
            "第1行: 对用户问题的理解\n"
            "第2行: 需要执行的操作\n"
            "然后每行一条 Redis 命令\n\n"
            "命令选择规则（必须遵守）：\n"
            "- 真实数据标注了每个键的类型，直接按类型选命令！\n"
            "- hash → HGETALL key\n"
            "- string → GET key\n"
            "- list → LRANGE key 0 -1\n"
            "- set → SMEMBERS key\n"
            "- 删除 → DEL key\n"
            "- 绝对禁止：TYPE命令、GET查hash、HGETALL查string. 选错命令会执行失败！"

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
        # 清理 markdown 代码块标记
        import re as _re
        cmd_text = _re.sub(r'```\w*\n?', '', req.command)
        cmd_text = _re.sub(r'```', '', cmd_text)

        results = []
        type_sensitive = {'GET': 'string', 'SET': 'string', 'APPEND': 'string', 'STRLEN': 'string',
                          'HGET': 'hash', 'HSET': 'hash', 'HGETALL': 'hash', 'HDEL': 'hash',
                          'LPUSH': 'list', 'RPUSH': 'list', 'LRANGE': 'list',
                          'SADD': 'set', 'SMEMBERS': 'set',
                          'ZADD': 'zset', 'ZRANGE': 'zset'}

        # 有效的 Redis 命令列表
        VALID_CMDS = {'GET','SET','DEL','EXISTS','EXPIRE','TTL','TYPE','KEYS','SCAN',
                      'HGET','HSET','HGETALL','HDEL','HLEN','HEXISTS','HKEYS','HVALS',
                      'LPUSH','RPUSH','LPOP','RPOP','LRANGE','LLEN','LINDEX','LSET',
                      'SADD','SREM','SMEMBERS','SISMEMBER','SCARD','SPOP',
                      'ZADD','ZREM','ZRANGE','ZRANK','ZCARD','ZSCORE',
                      'INCR','DECR','INCRBY','DECRBY','APPEND','STRLEN',
                      'RENAME','RENAMENX','MOVE','SELECT','DBSIZE','FLUSHDB','FLUSHALL',
                      'PERSIST','PEXPIRE','PEXPIREAT','PTTL','RESTORE','SORT',
                      'ECHO','PING','QUIT','INFO','CLIENT','CONFIG','SLOWLOG',
                      'PUBLISH','SUBSCRIBE','UNSUBSCRIBE','PUBSUB',
                      'MULTI','EXEC','DISCARD','WATCH','UNWATCH'}

        for line in cmd_text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            cmd = parts[0].upper()
            # 跳过非命令的分析文本
            if cmd not in VALID_CMDS:
                continue
            args = parts[1:]

            # 类型敏感命令: 先检查 key 类型
            expected = type_sensitive.get(cmd)
            if expected and args:
                t = r.type(args[0])
                if t != expected and t != 'none':
                    results.append(f'{cmd}: 类型错误 — {args[0]} 是 {t}, 需要 {expected}')
                    continue

            try:
                result = r.execute_command(cmd, *args)
                # 友好提示
                if cmd == 'DEL':
                    results.append(f'{cmd}: 已删除 {result} 个键' if result else f'{cmd}: 键不存在')
                else:
                    results.append(f'{cmd}: {result}')
            except Exception as e:
                results.append(f'{cmd}: ERROR - {e}')
        return {"ok": True, "result": '\n'.join(results)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
