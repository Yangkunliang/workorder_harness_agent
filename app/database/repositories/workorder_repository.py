"""
工单数据访问层
提供工单数据的增删改查操作
"""
from datetime import datetime
from typing import Optional, Tuple, List, Dict, Any

from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import Session

from app.database.models import Workorder


class WorkorderRepository:
    """工单数据访问层"""

    def __init__(self, db: Session):
        self.db = db

    def query(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        size: int = 20
    ) -> Tuple[List[Workorder], int]:
        """
        查询工单列表
        
        :param filters: 查询条件字典
        :param page: 页码（从1开始）
        :param size: 每页条数
        :return: (工单列表, 总数)
        """
        query = select(Workorder).filter(Workorder.is_deleted == False)

        # 工单编号精确查询（支持逗号分隔多个）
        workorder_no = filters.get("workorder_no")
        if workorder_no:
            nos = [n.strip() for n in workorder_no.split(",") if n.strip()]
            if nos:
                query = query.filter(Workorder.workorder_no.in_(nos))

        # 创建人前缀模糊匹配
        creator = filters.get("creator")
        if creator:
            query = query.filter(Workorder.creator.like(f"{creator}%"))

        # 创建时间范围查询
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Workorder.created_at >= start_datetime)
        if end_date:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
            # 包含结束日期的最后一秒
            end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
            query = query.filter(Workorder.created_at <= end_datetime)

        # 默认按创建时间倒序
        query = query.order_by(Workorder.created_at.desc())

        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        # 执行查询
        result = self.db.execute(query)
        workorders = result.scalars().all()

        # 查询总数
        count_query = select(func.count(Workorder.id)).filter(Workorder.is_deleted == False)
        if workorder_no:
            count_query = count_query.filter(Workorder.workorder_no.in_(nos))
        if creator:
            count_query = count_query.filter(Workorder.creator.like(f"{creator}%"))
        if start_date:
            count_query = count_query.filter(Workorder.created_at >= start_datetime)
        if end_date:
            count_query = count_query.filter(Workorder.created_at <= end_datetime)

        count_result = self.db.execute(count_query)
        total = count_result.scalar() or 0

        return workorders, total

    def get_by_no(self, workorder_no: str) -> Optional[Workorder]:
        """
        按工单编号查询单个工单
        
        :param workorder_no: 工单编号
        :return: 工单对象或None
        """
        query = select(Workorder).filter(
            Workorder.workorder_no == workorder_no,
            Workorder.is_deleted == False
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def get_by_nos(self, workorder_nos: List[str]) -> List[Workorder]:
        """
        批量按工单编号查询
        
        :param workorder_nos: 工单编号列表
        :return: 工单列表
        """
        query = select(Workorder).filter(
            Workorder.workorder_no.in_(workorder_nos),
            Workorder.is_deleted == False
        )
        result = self.db.execute(query)
        return result.scalars().all()
