"""
常量、枚举、错误码定义
"""
from enum import Enum


# ==================== 工单状态枚举 ====================

class WorkorderStatus(str, Enum):
    """工单状态"""
    NORMAL = "正常"
    CLOSED = "已关闭"
    DELETED = "已删除"


# ==================== 操作类型枚举 ====================

class OperationType(str, Enum):
    """操作类型"""
    QUERY = "query_workorder"
    CREATE = "create_workorder"
    URGE = "urge_workorder"
    CLOSE = "close_workorder"
    DELETE = "delete_workorder"


# ==================== 意图枚举 ====================

class IntentType(str, Enum):
    """用户意图类型"""
    QUERY = "query_workorder"
    CREATE = "create_workorder"
    URGE = "urge_workorder"
    CLOSE = "close_workorder"
    DELETE = "delete_workorder"
    CONFIRM = "confirm_execution"
    CANCEL = "cancel_execution"
    UNKNOWN = "unknown"


# ==================== 高危操作集合 ====================

RISK_OPERATIONS: set[str] = {OperationType.CLOSE, OperationType.DELETE}

# ==================== 普通操作集合 ====================

NORMAL_OPERATIONS: set[str] = {OperationType.QUERY, OperationType.CREATE, OperationType.URGE}

# ==================== 错误码 ====================

class ErrorCode(str, Enum):
    """统一错误码"""
    SUCCESS = "00000"
    VALIDATION_ERROR = "10001"
    PARAM_MISSING = "10002"
    ILLEGAL_PARAM = "10003"
    WORKORDER_NOT_FOUND = "20001"
    DUPLICATE_OPERATION = "20002"
    WORKORDER_STATUS_ERROR = "20003"
    RISK_OPERATION_DENIED = "30001"
    RISK_RATE_LIMIT = "30002"
    CIRCUIT_BREAKER_OPEN = "40001"
    SERVICE_DEGRADED = "40002"
    INFRA_ERROR = "50001"
    LLM_ERROR = "50002"
    UNKNOWN_ERROR = "99999"


# ==================== 错误文案映射 ====================

ERROR_MESSAGES: dict[str, str] = {
    ErrorCode.SUCCESS: "操作成功",
    ErrorCode.VALIDATION_ERROR: "参数校验失败",
    ErrorCode.PARAM_MISSING: "缺少必要参数",
    ErrorCode.ILLEGAL_PARAM: "参数非法",
    ErrorCode.WORKORDER_NOT_FOUND: "工单不存在",
    ErrorCode.DUPLICATE_OPERATION: "重复操作",
    ErrorCode.WORKORDER_STATUS_ERROR: "工单状态不允许此操作",
    ErrorCode.RISK_OPERATION_DENIED: "高危操作需要二次确认",
    ErrorCode.RISK_RATE_LIMIT: "操作过于频繁",
    ErrorCode.CIRCUIT_BREAKER_OPEN: "服务熔断中",
    ErrorCode.SERVICE_DEGRADED: "当前服务繁忙",
    ErrorCode.INFRA_ERROR: "基础设施异常",
    ErrorCode.LLM_ERROR: "AI 服务异常",
    ErrorCode.UNKNOWN_ERROR: "未知错误",
}

# ==================== 降级文案 ====================

DEGRADED_MESSAGE = "当前服务繁忙，请稍后再试"

# ==================== 高危操作确认话术 ====================

RISK_CONFIRM_TEMPLATES: dict[str, str] = {
    OperationType.CLOSE: (
        "⚠️ 高危操作提醒\n"
        "您正在执行【关闭工单】操作，工单编号：{workorder_id}\n"
        "此操作将使工单状态变更为'已关闭'，请确认是否继续。\n\n"
        "请回复【确认执行】继续操作，或回复【取消】终止操作。"
    ),
    OperationType.DELETE: (
        "⚠️ 高危操作提醒\n"
        "您正在执行【删除工单】操作，工单编号：{workorder_id}\n"
        "此操作将软删除该工单数据（数据可恢复），请确认是否继续。\n\n"
        "请回复【确认执行】继续操作，或回复【取消】终止操作。"
    ),
}

# ==================== 高危操作限流间隔（秒） ====================

RISK_OPERATION_INTERVAL: int = 60

# ==================== 催办冷却时间（秒） ====================

URGE_COOLDOWN_SECONDS: int = 300
