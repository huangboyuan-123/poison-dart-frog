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

        # 提取问题中提到的 key，查询真实数据
        import re as _re
        r = get_redis()
        data_context = ""
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
            except Exception:
                pass

        # 构建强约束提示
        if data_context:
            human_msg = (
                f"【真实数据 - 必须使用】{data_context}\n\n"
                f"【用户需求】{req.question}\n\n"
                f"请根据上面的真实数据生成 Redis 命令，禁止编造！"
            )
        else:
            human_msg = req.question

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
            "你是 Redis 专家。根据【真实数据】生成 Redis 命令，每条一行。"
            "Hash→HSET/HGET, String→SET/GET。改类型→DEL旧键→用真实数据HSET。"
            "禁止编造数据！必须使用【真实数据】中的值！"
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
        type_sensitive = {'HGET': 'hash', 'HSET': 'hash', 'HGETALL': 'hash', 'HDEL': 'hash',
                          'LPUSH': 'list', 'RPUSH': 'list', 'LRANGE': 'list',
                          'SADD': 'set', 'SMEMBERS': 'set',
                          'ZADD': 'zset', 'ZRANGE': 'zset'}

        for line in req.command.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            cmd = parts[0].upper()
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
                results.append(f'{cmd}: {result}')
            except Exception as e:
                results.append(f'{cmd}: ERROR - {e}')
        return {"ok": True, "result": '\n'.join(results)}
    except Exception as e:
        return {"ok": False, "error": str(e)}
