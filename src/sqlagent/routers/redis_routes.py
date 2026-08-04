"""
Redis 路由 — 键浏览、值读写、键删除。
"""

import os
from typing import Optional

import redis
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/redis", tags=["redis"])

# Redis 连接 (从环境变量读取)
_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
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
