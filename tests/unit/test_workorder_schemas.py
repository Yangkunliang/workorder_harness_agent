"""
工单 Pydantic 模型单元测试
测试 app/schemas/workorder.py 中的数据模型
"""
import pytest
from datetime import date
from pydantic import ValidationError

from app.schemas.workorder import (
    WorkorderQueryRequest,
    WorkorderResponse,
    WorkorderDetailResponse,
    PaginationResponse,
    WorkorderListResponse,
)


class TestWorkorderQueryRequest:
    """工单查询请求模型测试"""

    def test_default_values(self):
        """测试默认值"""
        request = WorkorderQueryRequest()
        
        assert request.page == 1
        assert request.size == 20
        assert request.workorder_no is None
        assert request.creator is None
        assert request.start_date is None
        assert request.end_date is None

    def test_with_values(self):
        """测试设置值"""
        request = WorkorderQueryRequest(
            page=2,
            size=50,
            workorder_no="WO001,WO002",
            creator="张",
            start_date="2025-06-01",
            end_date="2025-06-30"
        )
        
        assert request.page == 2
        assert request.size == 50
        assert request.workorder_no == "WO001,WO002"
        assert request.creator == "张"
        assert request.start_date == "2025-06-01"
        assert request.end_date == "2025-06-30"

    def test_page_validation(self):
        """测试页码验证（必须 >= 1）"""
        with pytest.raises(ValidationError):
            WorkorderQueryRequest(page=0)
        
        with pytest.raises(ValidationError):
            WorkorderQueryRequest(page=-1)

    def test_size_validation(self):
        """测试页大小验证（必须 1 <= size <= 100）"""
        with pytest.raises(ValidationError):
            WorkorderQueryRequest(size=0)
        
        with pytest.raises(ValidationError):
            WorkorderQueryRequest(size=101)


class TestWorkorderResponse:
    """工单响应模型测试"""

    def test_required_fields(self):
        """测试必填字段"""
        response = WorkorderResponse(
            workorder_no="WO001",
            title="测试工单",
            status="pending",
            creator="张三",
            created_at="2025-06-10T10:00:00",
            updated_at="2025-06-10T14:30:00"
        )
        
        assert response.workorder_no == "WO001"
        assert response.title == "测试工单"
        assert response.status == "pending"
        assert response.creator == "张三"
        assert response.created_at == "2025-06-10T10:00:00"
        assert response.updated_at == "2025-06-10T14:30:00"

    def test_missing_required_field(self):
        """测试缺少必填字段"""
        with pytest.raises(ValidationError):
            WorkorderResponse(
                workorder_no="WO001",
                title="测试工单",
                # 缺少其他必填字段
            )


class TestWorkorderDetailResponse:
    """工单详情响应模型测试"""

    def test_all_fields(self):
        """测试所有字段"""
        response = WorkorderDetailResponse(
            workorder_no="WO001",
            title="测试工单",
            status="completed",
            creator="李四",
            description="这是工单描述",
            created_at="2025-06-10T10:00:00",
            updated_at="2025-06-10T14:30:00"
        )
        
        assert response.workorder_no == "WO001"
        assert response.description == "这是工单描述"

    def test_empty_description(self):
        """测试空描述（允许为空）"""
        response = WorkorderDetailResponse(
            workorder_no="WO001",
            title="测试工单",
            status="pending",
            creator="王五",
            description="",
            created_at="2025-06-10T10:00:00",
            updated_at="2025-06-10T14:30:00"
        )
        
        assert response.description == ""


class TestPaginationResponse:
    """分页响应模型测试"""

    def test_pagination_fields(self):
        """测试分页字段"""
        pagination = PaginationResponse(
            page=1,
            size=20,
            total=45,
            pages=3
        )
        
        assert pagination.page == 1
        assert pagination.size == 20
        assert pagination.total == 45
        assert pagination.pages == 3


class TestWorkorderListResponse:
    """工单列表响应模型测试"""

    def test_list_with_pagination(self):
        """测试带分页的列表响应"""
        workorder = WorkorderResponse(
            workorder_no="WO001",
            title="测试工单",
            status="pending",
            creator="张三",
            created_at="2025-06-10T10:00:00",
            updated_at="2025-06-10T14:30:00"
        )
        
        pagination = PaginationResponse(
            page=1,
            size=20,
            total=1,
            pages=1
        )
        
        response = WorkorderListResponse(
            list=[workorder],
            pagination=pagination
        )
        
        assert len(response.list) == 1
        assert response.pagination.total == 1

    def test_empty_list(self):
        """测试空列表"""
        pagination = PaginationResponse(
            page=1,
            size=20,
            total=0,
            pages=0
        )
        
        response = WorkorderListResponse(
            list=[],
            pagination=pagination
        )
        
        assert len(response.list) == 0
        assert response.pagination.total == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
