"""
工具路由层（Harness 第2层）
- 统一转发、路由分发
- 根据 tool_id 路由到对应的业务处理函数
"""
from typing import Any, Callable

from app.common.exceptions import ValidationException
from app.common.logger import business_logger
from app.schemas.tool_schema import ToolExecutionResult


class ToolRouter:
    """工具路由器：根据 tool_id 分发到对应的处理函数"""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable] = {}

    def register(self, tool_id: str, handler: Callable) -> None:
        """注册工具处理函数"""
        self._handlers[tool_id] = handler
        business_logger.info(f"路由注册: {tool_id} -> {handler.__name__}")

    def route(self, tool_id: str, params: dict[str, Any], **kwargs: Any) -> ToolExecutionResult:
        """根据 tool_id 路由到对应处理函数"""
        handler = self._handlers.get(tool_id)
        if not handler:
            raise ValidationException(f"未找到工具 {tool_id} 的处理函数")

        business_logger.info(f"路由分发: {tool_id}", params=list(params.keys()))
        return handler(params, **kwargs)

    def get_registered_tools(self) -> list[str]:
        """获取已注册的工具列表"""
        return list(self._handlers.keys())


# 全局路由器实例
tool_router = ToolRouter()
