"""
工具执行代理层（Harness 第5层）
- 对接本地 MySQL 业务接口
- 编排5层 Harness 调用链路：校验 → 路由 → 注册中心 → 容错 → 执行
- 统一入口，对外提供 execute_tool 方法
"""
from typing import Any

from app.common.exceptions import ValidationException
from app.common.logger import business_logger
from app.schemas.tool_schema import ToolExecutionRequest, ToolExecutionResult


class ToolExecutor:
    """工具执行代理：编排 Harness 5层调用链路"""

    async def execute(self, request: ToolExecutionRequest) -> ToolExecutionResult:
        """
        执行工具调用，完整走 Harness 5层链路：
        1. 输入校验层
        2. 工具注册中心查询
        3. 容错治理层（重试 + 熔断）
        4. 工具路由层
        5. 实际业务执行
        """
        from app.harness.validator import input_validator
        from app.harness.registry import tool_registry
        from app.harness.governance import governance_executor
        from app.harness.router import tool_router

        tool_id = request.tool_id
        business_logger.info(
            "Harness 执行开始",
            tool_id=tool_id,
            session_id=request.session_id,
            user_id=request.user_id,
        )

        # 第1层：输入校验
        try:
            validated_params = input_validator.validate(request)
        except Exception as e:
            business_logger.error(f"输入校验失败: {str(e)}", tool_id=tool_id)
            return ToolExecutionResult(
                tool_id=tool_id,
                success=False,
                error_code=getattr(e, "error_code", "VALIDATION_ERROR"),
                error_message=getattr(e, "message", str(e)),
            )

        # 第2层：注册中心查询
        tool_config = tool_registry.get_tool(tool_id)
        if not tool_config:
            return ToolExecutionResult(
                tool_id=tool_id,
                success=False,
                error_code="TOOL_NOT_FOUND",
                error_message=f"未注册的工具：{tool_id}",
            )

        # 第3+4层：容错治理 + 路由执行
        def _route_and_execute(**kwargs: Any) -> ToolExecutionResult:
            """路由到具体处理函数并执行"""
            return tool_router.route(tool_id, validated_params, **kwargs)

        result = governance_executor.execute_with_governance(
            tool_id=tool_id,
            func=_route_and_execute,
            session_id=request.session_id,
            user_id=request.user_id,
            ip_address=request.ip_address,
        )

        business_logger.info(
            "Harness 执行完成",
            tool_id=tool_id,
            success=result.success,
        )
        return result


# 全局执行器实例
tool_executor = ToolExecutor()
