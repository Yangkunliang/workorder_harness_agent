"""
Redis 异步客户端单例
- 全局复用连接，避免每次请求新建
- 供 checkpointer 和业务层统一使用
"""
import os
import redis.asyncio as aioredis

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """获取全局 Redis 异步客户端（懒初始化单例）"""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.Redis(
            host=os.getenv("REDIS_HOST", "127.0.0.1"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD") or None,
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=False,  # checkpointer 需要 bytes 模式
        )
    return _redis_client


async def close_redis_client() -> None:
    """关闭 Redis 连接（在 FastAPI lifespan 关闭阶段调用）"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
