"""
企业级 Harness 架构 AI 工单 Agent - 项目启动入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.nacos_config import nacos_manager
from app.database.session import init_database
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 生命周期管理：启动时初始化，关闭时清理资源"""
    # 启动阶段
    print("[Startup] 正在初始化数据库...")
    await init_database()
    print("[Startup] 数据库初始化完成")

    print("[Startup] 正在连接 Nacos 并拉取工具配置...")
    await nacos_manager.init()
    print("[Startup] Nacos 工具配置加载完成")

    # 初始化工具注册中心内存缓存
    from app.harness.registry import tool_registry
    await tool_registry.init()
    print("[Startup] 工具注册中心初始化完成")

    # 注册工具路由处理函数（同步包装器，供 Harness 路由层调用）
    from app.harness.router import tool_router
    from app.services.workorder_service import workorder_service

    def _make_handler(tool_id: str):
        """创建工具处理函数（同步包装异步）"""
        def handler(params: dict, **kwargs):
            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                # 在已有事件循环中，创建任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        workorder_service.execute(tool_id, params, **kwargs)
                    )
                    return future.result()
            else:
                return asyncio.run(workorder_service.execute(tool_id, params, **kwargs))
        return handler

    tool_router.register("workorder_query", _make_handler("workorder_query"))
    tool_router.register("workorder_create", _make_handler("workorder_create"))
    tool_router.register("workorder_urge", _make_handler("workorder_urge"))
    tool_router.register("workorder_close", _make_handler("workorder_close"))
    tool_router.register("workorder_delete", _make_handler("workorder_delete"))
    print("[Startup] 工具路由注册完成")

    print("[Startup] 服务启动完成，端口: 8000")
    yield

    # 关闭阶段
    print("[Shutdown] 正在清理资源...")
    await nacos_manager.close()
    print("[Shutdown] 资源清理完成")


app = FastAPI(
    title="企业级 Harness 架构 AI 工单 Agent",
    description="基于 LangGraph + Harness 六层架构的企业工单智能助手",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    import os
    from dotenv import load_dotenv

    load_dotenv()
    port = int(os.getenv("SERVER_PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
