"""
工单业务服务层
- 工单 CRUD 操作
- 催办逻辑
- 高危操作（关闭/删除）软删除实现
- 直接操作 MySQL 数据库
"""
import os
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.constants import WorkorderStatus, OperationType, URGE_COOLDOWN_SECONDS
from app.common.exceptions import (
    WorkorderNotFoundException,
    WorkorderStatusException,
    DuplicateOperationException,
)
from app.common.logger import business_logger
from app.database.session import async_session
from app.database.models import Workorder


class WorkorderService:
    """工单业务服务"""

    async def execute(
        self,
        tool_id: str,
        params: dict[str, Any],
        session_id: str = "",
        user_id: str = "",
        ip_address: str = "",
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """根据 tool_id 执行对应的业务操作"""
        handler_map = {
            "workorder_query": self.query_workorder,
            "workorder_create": self.create_workorder,
            "workorder_urge": self.urge_workorder,
            "workorder_close": self.close_workorder,
            "workorder_delete": self.delete_workorder,
        }
        handler = handler_map.get(tool_id)
        if not handler:
            raise ValueError(f"未知的工具ID: {tool_id}")

        async with async_session() as db:
            return await handler(db, params, session_id, user_id, ip_address)

    async def query_workorder(
        self,
        db: AsyncSession,
        params: dict[str, Any],
        session_id: str = "",
        user_id: str = "",
        ip_address: str = "",
    ) -> list[dict[str, Any]] | dict[str, Any]:
        """查询工单"""
        workorder_id = params.get("workorder_id")
        create_user = params.get("create_user")
        status = params.get("status")

        if workorder_id:
            # 按工单编号精确查询
            result = await db.execute(
                select(Workorder).where(
                    Workorder.workorder_id == workorder_id,
                    Workorder.is_deleted == False,
                )
            )
            wo = result.scalars().first()
            if not wo:
                raise WorkorderNotFoundException(workorder_id)
            return self._to_dict(wo)
        else:
            # 按创建人/状态模糊查询
            query = select(Workorder).where(Workorder.is_deleted == False)
            if create_user:
                query = query.where(Workorder.create_user == create_user)
            if status:
                query = query.where(Workorder.status == status)
            query = query.order_by(Workorder.create_time.desc()).limit(20)
            result = await db.execute(query)
            workorders = result.scalars().all()
            if not workorders:
                # 获取可用的用户列表
                user_result = await db.execute(select(Workorder.create_user).distinct().where(Workorder.is_deleted == False))
                available_users = [row[0] for row in user_result.all()]
                raise WorkorderNotFoundException(available_users=available_users)
            return [self._to_dict(wo) for wo in workorders]

    async def create_workorder(
        self,
        db: AsyncSession,
        params: dict[str, Any],
        session_id: str = "",
        user_id: str = "",
        ip_address: str = "",
    ) -> dict[str, Any]:
        """新建工单"""
        title = params["title"]
        content = params["content"]
        create_user = params["create_user"]

        # 生成工单编号：WO+年月日+4位序号
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")

        # 查询当天最大序号
        result = await db.execute(
            select(Workorder).where(
                Workorder.workorder_id.like(f"WO{date_str}%")
            ).order_by(Workorder.workorder_id.desc())
        )
        last_wo = result.scalars().first()
        if last_wo:
            last_seq = int(last_wo.workorder_id[-4:])
            new_seq = last_seq + 1
        else:
            new_seq = 1

        workorder_id = f"WO{date_str}{new_seq:04d}"

        wo = Workorder(
            workorder_id=workorder_id,
            title=title,
            content=content,
            create_user=create_user,
            status=WorkorderStatus.NORMAL,
            create_time=now,
            update_time=now,
            is_deleted=False,
        )
        db.add(wo)
        await db.commit()
        await db.refresh(wo)

        business_logger.info(f"新建工单成功: {workorder_id}")
        return self._to_dict(wo)

    async def urge_workorder(
        self,
        db: AsyncSession,
        params: dict[str, Any],
        session_id: str = "",
        user_id: str = "",
        ip_address: str = "",
    ) -> dict[str, Any]:
        """工单催办"""
        workorder_id = params["workorder_id"]

        # 查询工单
        result = await db.execute(
            select(Workorder).where(
                Workorder.workorder_id == workorder_id,
                Workorder.is_deleted == False,
            )
        )
        wo = result.scalars().first()
        if not wo:
            raise WorkorderNotFoundException(workorder_id)

        if wo.status != WorkorderStatus.NORMAL:
            raise WorkorderStatusException("只有正常状态的工单才能催办")

        # 催办冷却检查（Redis）
        try:
            import redis as redis_lib
            r = redis_lib.Redis(
                host=os.getenv("REDIS_HOST", "127.0.0.1"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD") or None,
                db=int(os.getenv("REDIS_DB", "0")),
            )
            urge_key = f"urge_cooldown:{workorder_id}"
            if r.exists(urge_key):
                raise DuplicateOperationException("该工单5分钟内已催办，请稍后再试")
            r.setex(urge_key, URGE_COOLDOWN_SECONDS, "1")
        except DuplicateOperationException:
            raise
        except Exception as e:
            business_logger.warning(f"催办冷却检查异常（放行）: {str(e)}")

        urge_time = datetime.now().isoformat()
        business_logger.info(f"工单催办成功: {workorder_id}")

        return {
            "workorder_id": workorder_id,
            "urge_time": urge_time,
            "status": wo.status,
        }

    async def close_workorder(
        self,
        db: AsyncSession,
        params: dict[str, Any],
        session_id: str = "",
        user_id: str = "",
        ip_address: str = "",
    ) -> dict[str, Any]:
        """关闭工单（高危操作）"""
        workorder_id = params["workorder_id"]

        result = await db.execute(
            select(Workorder).where(
                Workorder.workorder_id == workorder_id,
                Workorder.is_deleted == False,
            )
        )
        wo = result.scalars().first()
        if not wo:
            raise WorkorderNotFoundException(workorder_id)

        if wo.status != WorkorderStatus.NORMAL:
            raise WorkorderStatusException("只有正常状态的工单才能关闭")

        wo.status = WorkorderStatus.CLOSED
        wo.update_time = datetime.now()
        await db.commit()

        business_logger.info(f"关闭工单成功: {workorder_id}")
        return self._to_dict(wo)

    async def delete_workorder(
        self,
        db: AsyncSession,
        params: dict[str, Any],
        session_id: str = "",
        user_id: str = "",
        ip_address: str = "",
    ) -> dict[str, Any]:
        """删除工单（高危操作，软删除）"""
        workorder_id = params["workorder_id"]

        result = await db.execute(
            select(Workorder).where(
                Workorder.workorder_id == workorder_id,
                Workorder.is_deleted == False,
            )
        )
        wo = result.scalars().first()
        if not wo:
            raise WorkorderNotFoundException(workorder_id)

        # 软删除：设置 is_deleted=True, status=已删除
        wo.is_deleted = True
        wo.status = WorkorderStatus.DELETED
        wo.update_time = datetime.now()
        await db.commit()

        business_logger.info(f"删除工单成功（软删除）: {workorder_id}")
        return {"workorder_id": workorder_id, "status": WorkorderStatus.DELETED}

    @staticmethod
    def _to_dict(wo: Workorder) -> dict[str, Any]:
        """ORM 对象转字典"""
        return {
            "workorder_id": wo.workorder_id,
            "title": wo.title,
            "content": wo.content,
            "create_user": wo.create_user,
            "status": wo.status,
            "create_time": wo.create_time.isoformat() if wo.create_time else "",
            "update_time": wo.update_time.isoformat() if wo.update_time else "",
        }


# 全局服务实例
workorder_service = WorkorderService()
