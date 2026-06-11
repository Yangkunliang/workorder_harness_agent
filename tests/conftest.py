"""
Pytest 配置文件
"""
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop_policy():
    """使用默认的事件循环策略"""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function", autouse=True)
async def cleanup_database():
    """每个测试后清理数据库连接"""
    yield
    # 清理连接池
    try:
        from app.database.session import engine
        await engine.dispose()
    except:
        pass
