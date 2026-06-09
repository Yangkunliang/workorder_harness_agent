"""
自定义业务异常体系
- 分层异常设计：基础设施异常、业务异常、校验异常
- 统一错误码规范
"""


class BaseAppException(Exception):
    """应用基础异常"""

    def __init__(self, error_code: str, message: str, detail: str = "") -> None:
        self.error_code = error_code
        self.message = message
        self.detail = detail
        super().__init__(f"[{error_code}] {message}")


# ==================== 校验异常 ====================

class ValidationException(BaseAppException):
    """参数校验异常"""

    def __init__(self, message: str = "参数校验失败", detail: str = "") -> None:
        super().__init__(error_code="VALIDATION_ERROR", message=message, detail=detail)


class ParamMissingException(BaseAppException):
    """参数缺失异常"""

    def __init__(self, param_name: str, detail: str = "") -> None:
        super().__init__(
            error_code="PARAM_MISSING",
            message=f"缺少必要参数：{param_name}",
            detail=detail,
        )


class IllegalParamException(BaseAppException):
    """非法参数异常"""

    def __init__(self, message: str = "参数非法", detail: str = "") -> None:
        super().__init__(error_code="ILLEGAL_PARAM", message=message, detail=detail)


# ==================== 业务异常 ====================

class WorkorderNotFoundException(BaseAppException):
    """工单不存在异常"""

    def __init__(self, workorder_id: str = "", detail: str = "", available_users: list = None) -> None:
        msg = f"未找到编号为 {workorder_id} 的工单" if workorder_id else "工单不存在"
        super().__init__(error_code="WORKORDER_NOT_FOUND", message=msg, detail=detail)
        self.available_users = available_users or []


class DuplicateOperationException(BaseAppException):
    """重复操作异常"""

    def __init__(self, message: str = "该操作已执行，请勿重复提交", detail: str = "") -> None:
        super().__init__(error_code="DUPLICATE_OPERATION", message=message, detail=detail)


class RiskOperationDeniedException(BaseAppException):
    """高危操作未确认异常"""

    def __init__(self, message: str = "高危操作需要二次确认", detail: str = "") -> None:
        super().__init__(error_code="RISK_OPERATION_DENIED", message=message, detail=detail)


class RiskRateLimitException(BaseAppException):
    """高危操作限流异常"""

    def __init__(self, message: str = "操作过于频繁，请稍后再试", detail: str = "") -> None:
        super().__init__(error_code="RISK_RATE_LIMIT", message=message, detail=detail)


class WorkorderStatusException(BaseAppException):
    """工单状态异常"""

    def __init__(self, message: str = "工单状态不允许此操作", detail: str = "") -> None:
        super().__init__(error_code="WORKORDER_STATUS_ERROR", message=message, detail=detail)


# ==================== 基础设施异常 ====================

class InfrastructureException(BaseAppException):
    """基础设施异常（数据库、Redis、Nacos 等）"""

    def __init__(self, message: str = "基础设施异常", detail: str = "") -> None:
        super().__init__(error_code="INFRA_ERROR", message=message, detail=detail)


class CircuitBreakerOpenException(BaseAppException):
    """熔断器开启异常"""

    def __init__(self, tool_id: str = "", detail: str = "") -> None:
        msg = f"工具 {tool_id} 当前处于熔断状态，请稍后再试" if tool_id else "服务熔断中，请稍后再试"
        super().__init__(error_code="CIRCUIT_BREAKER_OPEN", message=msg, detail=detail)


class ServiceDegradedException(BaseAppException):
    """服务降级异常"""

    def __init__(self, message: str = "当前服务繁忙，请稍后再试", detail: str = "") -> None:
        super().__init__(error_code="SERVICE_DEGRADED", message=message, detail=detail)


class LLMException(BaseAppException):
    """LLM 调用异常"""

    def __init__(self, message: str = "AI 服务异常，请稍后重试", detail: str = "") -> None:
        super().__init__(error_code="LLM_ERROR", message=message, detail=detail)
