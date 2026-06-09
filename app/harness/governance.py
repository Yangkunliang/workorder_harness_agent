"""
异常容错治理层（Harness 第4层）
- 分级重试（tenacity）：可重试场景指数退避，禁止无效重试
- 熔断器（pybreaker）：连续失败触发熔断，半开试探
- 错误码拦截：禁止对业务错误重试
- 降级：熔断后返回友好降级文案
"""
from typing import Any, Callable

import pybreaker
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
)

from app.common.exceptions import (
    CircuitBreakerOpenException,
    ServiceDegradedException,
    BaseAppException,
    ValidationException,
    ParamMissingException,
    IllegalParamException,
    WorkorderNotFoundException,
    DuplicateOperationException,
    RiskOperationDeniedException,
    RiskRateLimitException,
    WorkorderStatusException,
)
from app.common.constants import DEGRADED_MESSAGE
from app.common.logger import business_logger, exception_logger
from app.schemas.tool_schema import ToolExecutionResult


# ==================== 不可重试异常集合 ====================

NON_RETRYABLE_EXCEPTIONS = (
    ValidationException,
    ParamMissingException,
    IllegalParamException,
    WorkorderNotFoundException,
    DuplicateOperationException,
    RiskOperationDeniedException,
    RiskRateLimitException,
    WorkorderStatusException,
)


def _is_retryable(exc: BaseException) -> bool:
    """判断异常是否可重试"""
    # 业务异常不重试
    if isinstance(exc, NON_RETRYABLE_EXCEPTIONS):
        return False
    # HTTP 4xx 不重试
    if hasattr(exc, "status_code") and isinstance(getattr(exc, "status_code"), int):
        code = getattr(exc, "status_code")
        if 400 <= code < 500:
            return False
    # 其他异常（5xx、网络异常等）可重试
    return True


# ==================== 熔断器管理 ====================

class CircuitBreakerManager:
    """熔断器管理器：每个工具独立熔断器"""

    def __init__(self) -> None:
        self._breakers: dict[str, pybreaker.CircuitBreaker] = {}

    def get_breaker(self, tool_id: str, fail_max: int = 5, reset_timeout: int = 30) -> pybreaker.CircuitBreaker:
        """获取或创建工具对应的熔断器"""
        if tool_id not in self._breakers:
            self._breakers[tool_id] = pybreaker.CircuitBreaker(
                fail_max=fail_max,
                reset_timeout=reset_timeout,
                name=f"breaker_{tool_id}",
            )
        return self._breakers[tool_id]

    def is_open(self, tool_id: str) -> bool:
        """检查熔断器是否开启"""
        breaker = self._breakers.get(tool_id)
        return breaker is not None and breaker.current_state == "open"


circuit_breaker_manager = CircuitBreakerManager()


# ==================== 容错执行器 ====================

class GovernanceExecutor:
    """容错治理执行器：集成重试 + 熔断 + 降级"""

    def execute_with_governance(
        self,
        tool_id: str,
        func: Callable,
        **kwargs: Any,
    ) -> ToolExecutionResult:
        """带容错治理的执行"""
        # 1. 检查熔断状态
        if circuit_breaker_manager.is_open(tool_id):
            business_logger.warning(f"工具 {tool_id} 熔断中，执行降级")
            return ToolExecutionResult(
                tool_id=tool_id,
                success=False,
                error_code="CIRCUIT_BREAKER_OPEN",
                error_message=DEGRADED_MESSAGE,
            )

        # 2. 获取工具配置
        from app.harness.registry import tool_registry
        max_retry = tool_registry.get_tool_max_retry(tool_id)
        circuit_threshold = tool_registry.get_tool_circuit_threshold(tool_id)

        # 3. 获取熔断器
        breaker = circuit_breaker_manager.get_breaker(
            tool_id,
            fail_max=circuit_threshold,
            reset_timeout=30,
        )

        # 4. 带重试 + 熔断执行
        try:
            result = self._execute_with_retry(
                tool_id=tool_id,
                func=func,
                max_retry=max_retry,
                breaker=breaker,
                **kwargs,
            )
            return result
        except pybreaker.CircuitBreakerError:
            exception_logger.error(f"工具 {tool_id} 熔断触发", tool_id=tool_id)
            return ToolExecutionResult(
                tool_id=tool_id,
                success=False,
                error_code="CIRCUIT_BREAKER_OPEN",
                error_message=DEGRADED_MESSAGE,
            )
        except NON_RETRYABLE_EXCEPTIONS as e:
            # 业务异常直接返回，不重试
            exception_logger.error(f"工具 {tool_id} 业务异常: {e.message}", tool_id=tool_id, error_code=e.error_code)
            return ToolExecutionResult(
                tool_id=tool_id,
                success=False,
                error_code=e.error_code,
                error_message=e.message,
            )
        except Exception as e:
            exception_logger.error(f"工具 {tool_id} 未知异常: {str(e)}", tool_id=tool_id)
            return ToolExecutionResult(
                tool_id=tool_id,
                success=False,
                error_code="UNKNOWN_ERROR",
                error_message=DEGRADED_MESSAGE,
            )

    def _execute_with_retry(
        self,
        tool_id: str,
        func: Callable,
        max_retry: int,
        breaker: pybreaker.CircuitBreaker,
        **kwargs: Any,
    ) -> ToolExecutionResult:
        """带重试的执行（通过熔断器）"""

        # 定义重试装饰器
        @retry(
            stop=stop_after_attempt(max_retry + 1),  # max_retry=0 时不重试
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception(_is_retryable),
            before_sleep=before_sleep_log(business_logger.logger, logging_level=30),  # WARNING
            reraise=True,
        )
        def _do_execute() -> ToolExecutionResult:
            try:
                result = breaker.call(func, **kwargs)
                if isinstance(result, ToolExecutionResult):
                    return result
                return ToolExecutionResult(tool_id=tool_id, success=True, data=result)
            except NON_RETRYABLE_EXCEPTIONS:
                raise  # 业务异常直接抛出，不进入重试
            except Exception as e:
                business_logger.warning(f"工具 {tool_id} 执行异常，可能重试: {str(e)}")
                raise

        return _do_execute()


# 全局容错治理执行器
governance_executor = GovernanceExecutor()
