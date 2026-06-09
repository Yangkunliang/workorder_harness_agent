"""
工具注册中心 Schema 定义
- 与 Nacos 工具注册中心配置一一对应
"""
from typing import Any, Optional

from pydantic import BaseModel, Field


class ToolRequestSchema(BaseModel):
    """工具请求参数 Schema"""
    type: str = Field(default="object", description="参数类型")
    properties: dict[str, Any] = Field(default_factory=dict, description="参数属性定义")
    required: list[str] = Field(default_factory=list, description="必填参数列表")


class ToolConfig(BaseModel):
    """工具注册中心配置模型"""
    tool_id: str = Field(..., description="工具唯一标识")
    tool_name: str = Field(..., description="工具名称")
    request_schema: dict[str, Any] = Field(default_factory=dict, description="请求参数 Schema")
    target_url: str = Field(..., description="目标接口地址")
    timeout: int = Field(default=5000, description="超时时间(ms)")
    max_retry: int = Field(default=2, description="最大重试次数")
    circuit_threshold: int = Field(default=5, description="熔断阈值（连续失败次数）")
    permission_tags: list[str] = Field(default_factory=list, description="权限标签")
    qps_limit: int = Field(default=50, description="QPS 限流")
    status: str = Field(default="active", description="工具状态：active/disabled")


class ToolExecutionRequest(BaseModel):
    """工具执行请求"""
    tool_id: str = Field(..., description="工具ID")
    params: dict[str, Any] = Field(default_factory=dict, description="执行参数")
    session_id: str = Field(default="", description="会话ID")
    user_id: str = Field(default="", description="用户ID")
    ip_address: str = Field(default="", description="IP地址")


class ToolExecutionResult(BaseModel):
    """工具执行结果"""
    tool_id: str = Field(..., description="工具ID")
    success: bool = Field(..., description="是否成功")
    data: Optional[Any] = Field(default=None, description="返回数据")
    error_code: Optional[str] = Field(default=None, description="错误码")
    error_message: Optional[str] = Field(default=None, description="错误信息")
