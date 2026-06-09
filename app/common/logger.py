"""
结构化日志模块
- 区分业务日志、审计日志、异常日志
- 统一 JSON 格式输出
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any


class StructuredFormatter(logging.Formatter):
    """结构化日志格式器，输出 JSON 格式"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        # 附加自定义字段
        if hasattr(record, "extra_data") and record.extra_data:
            log_data.update(record.extra_data)
        # 异常信息
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = str(record.exc_info[1])
        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """结构化日志器，支持业务日志、审计日志、异常日志分离"""

    def __init__(self, name: str, level: int = logging.INFO) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(handler)

    def info(self, message: str, **kwargs: Any) -> None:
        self.logger.info(message, extra={"extra_data": kwargs})

    def warning(self, message: str, **kwargs: Any) -> None:
        self.logger.warning(message, extra={"extra_data": kwargs})

    def error(self, message: str, **kwargs: Any) -> None:
        self.logger.error(message, extra={"extra_data": kwargs}, exc_info=True)

    def debug(self, message: str, **kwargs: Any) -> None:
        self.logger.debug(message, extra={"extra_data": kwargs})


# ==================== 全局日志实例 ====================

# 业务日志
business_logger = StructuredLogger("business")

# 审计日志（高危操作专用）
audit_logger = StructuredLogger("audit")

# 异常日志
exception_logger = StructuredLogger("exception")


def log_audit(
    session_id: str,
    user_id: str,
    workorder_id: str,
    operation_type: str,
    is_risk: bool,
    operation_result: str,
    ip_address: str = "",
) -> None:
    """记录审计日志（高危操作强制调用）"""
    audit_logger.info(
        "审计日志",
        session_id=session_id,
        user_id=user_id,
        workorder_id=workorder_id,
        operation_type=operation_type,
        is_risk=is_risk,
        operation_result=operation_result,
        ip_address=ip_address,
    )
