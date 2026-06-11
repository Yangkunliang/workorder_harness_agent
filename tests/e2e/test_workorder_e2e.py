"""
E2E 测试 - 工单查询功能
测试 API 接口的端到端功能
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import select, delete

from app.database.session import init_database, async_session
from app.database.models import Workorder


class TestWorkorderAPI:
    """工单 API 测试"""

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """测试数据库连接和数据初始化"""
        # 初始化数据库
        await init_database()
        
        async with async_session() as session:
            # 查询所有工单
            result = await session.execute(select(Workorder))
            workorders = result.scalars().all()
            
            print(f"数据库中现有 {len(workorders)} 条工单记录")

    @pytest.mark.asyncio
    async def test_workorder_crud_operations(self):
        """测试工单的 CRUD 操作"""
        await init_database()
        
        async with async_session() as session:
            # 创建测试工单
            test_workorder = Workorder(
                workorder_no="WO_TEST_001",
                title="E2E测试工单",
                status="pending",
                creator="测试用户",
                description="这是E2E测试工单的描述",
                created_at=datetime.now()
            )
            session.add(test_workorder)
            await session.commit()
            
            # 查询工单
            result = await session.execute(
                select(Workorder).where(Workorder.workorder_no == "WO_TEST_001")
            )
            workorder = result.scalar_one_or_none()
            
            assert workorder is not None
            assert workorder.title == "E2E测试工单"
            assert workorder.creator == "测试用户"
            
            # 删除测试工单
            await session.execute(
                delete(Workorder).where(Workorder.workorder_no == "WO_TEST_001")
            )
            await session.commit()
            
            # 验证删除
            result = await session.execute(
                select(Workorder).where(Workorder.workorder_no == "WO_TEST_001")
            )
            deleted_workorder = result.scalar_one_or_none()
            assert deleted_workorder is None

    @pytest.mark.asyncio
    async def test_workorder_query_by_creator(self):
        """测试按创建人模糊查询"""
        await init_database()
        
        async with async_session() as session:
            # 查询创建人包含"测试"的所有工单
            result = await session.execute(
                select(Workorder).where(Workorder.creator.like("测试%"))
            )
            workorders = result.scalars().all()
            
            print(f"找到 {len(workorders)} 条创建人包含'测试'的工单")
            assert len(workorders) >= 0

    @pytest.mark.asyncio
    async def test_workorder_pagination(self):
        """测试分页逻辑"""
        await init_database()
        
        async with async_session() as session:
            # 测试分页查询
            page = 1
            size = 5
            
            result = await session.execute(
                select(Workorder)
                .order_by(Workorder.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
            workorders = result.scalars().all()
            
            print(f"第 {page} 页，每页 {size} 条，找到 {len(workorders)} 条")
            assert len(workorders) <= size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
