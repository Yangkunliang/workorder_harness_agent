"""
工单相关的数据模型
"""
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class WorkorderQueryRequest(BaseModel):
    """
    工单查询请求模型
    """
    page: int = Field(1, ge=1, description="页码（从1开始）")
    size: int = Field(20, ge=1, le=100, description="每页条数（最大100）")
    workorder_no: Optional[str] = Field(None, description="工单编号（支持逗号分隔多个）")
    creator: Optional[str] = Field(None, description="创建人（前缀匹配）")
    start_date: Optional[str] = Field(None, description="开始日期（格式：YYYY-MM-DD）")
    end_date: Optional[str] = Field(None, description="结束日期（格式：YYYY-MM-DD）")


class WorkorderResponse(BaseModel):
    """
    工单列表响应模型
    """
    workorder_no: str = Field(..., description="工单编号")
    title: str = Field(..., description="工单标题")
    status: str = Field(..., description="工单状态")
    creator: str = Field(..., description="创建人（已脱敏）")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class WorkorderDetailResponse(BaseModel):
    """
    工单详情响应模型（不脱敏）
    """
    workorder_no: str = Field(..., description="工单编号")
    title: str = Field(..., description="工单标题")
    status: str = Field(..., description="工单状态")
    creator: str = Field(..., description="创建人")
    description: str = Field("", description="工单描述")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class PaginationResponse(BaseModel):
    """
    分页信息响应模型
    """
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页条数")
    total: int = Field(..., description="总记录数")
    pages: int = Field(..., description="总页数")


class WorkorderListResponse(BaseModel):
    """
    工单列表响应模型（包含分页）
    """
    list: List[WorkorderResponse] = Field(..., description="工单列表")
    pagination: PaginationResponse = Field(..., description="分页信息")
