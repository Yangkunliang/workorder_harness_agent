"""
响应模型定义
"""
from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import ErrorCode


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="Agent 回复消息")
    intent: Optional[str] = Field(default=None, description="识别的意图")
    need_confirm: bool = Field(default=False, description="是否需要二次确认")
    data: Optional[Any] = Field(default=None, description="附加数据")


class ApiResponse(BaseModel):
    """统一 API 响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "00000",
                "message": "操作成功",
                "data": {},
                "timestamp": 1699999999,
            }
        }
    )
    code: str = Field(default=ErrorCode.SUCCESS, description="错误码")
    message: str = Field(default="操作成功", description="错误信息")
    data: Optional[Any] = Field(default=None, description="业务数据")
    timestamp: int = Field(default_factory=lambda: int(datetime.now().timestamp()), description="响应时间戳")

    @classmethod
    def success(cls, data: Any = None, message: str = "操作成功") -> "ApiResponse":
        """创建成功响应"""
        return cls(
            code=ErrorCode.SUCCESS,
            message=message,
            data=data,
        )

    @classmethod
    def error(cls, code: str, message: str) -> "ApiResponse":
        """创建错误响应"""
        return cls(
            code=code,
            message=message,
            data=None,
        )


class WorkorderResponse(BaseModel):
    """工单信息响应"""
    workorder_id: str = Field(..., description="工单编号")
    title: str = Field(..., description="工单标题")
    content: str = Field(..., description="工单内容")
    create_user: str = Field(..., description="创建人")
    status: str = Field(..., description="工单状态")
    create_time: str = Field(..., description="创建时间")
    update_time: str = Field(..., description="更新时间")
