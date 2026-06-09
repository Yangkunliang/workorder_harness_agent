"""
请求模型定义
"""
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """用户对话请求"""
    session_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户ID")
    message: str = Field(..., description="用户输入消息")
    ip_address: str = Field(default="", description="用户IP地址")


class WorkorderQueryRequest(BaseModel):
    """查询工单请求"""
    workorder_id: Optional[str] = Field(default=None, description="工单编号")
    create_user: Optional[str] = Field(default=None, description="创建人")
    status: Optional[str] = Field(default=None, description="工单状态")


class WorkorderCreateRequest(BaseModel):
    """新建工单请求"""
    title: str = Field(..., min_length=1, max_length=200, description="工单标题")
    content: str = Field(..., min_length=1, max_length=5000, description="工单内容")
    create_user: str = Field(..., min_length=1, max_length=50, description="创建人")


class WorkorderUrgeRequest(BaseModel):
    """工单催办请求"""
    workorder_id: str = Field(..., description="工单编号")


class WorkorderCloseRequest(BaseModel):
    """关闭工单请求"""
    workorder_id: str = Field(..., description="工单编号")


class WorkorderDeleteRequest(BaseModel):
    """删除工单请求"""
    workorder_id: str = Field(..., description="工单编号")
