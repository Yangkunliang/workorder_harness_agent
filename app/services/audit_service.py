"""
审计日志服务层
- 高危操作审计日志写入
- 审计日志查询
"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.logger import business_logger
from app.database.session import async_session
from app.database.models import OperationAuditLog


class AuditService:
    """审计日志服务"""

    async def write_audit_log(
        self,
        session_id: str,
        user_id: str,
        workorder_id: str,
        operation_type: str,
        is_risk: bool,
        operation_result: str,
        ip_address: str = "",
    ) -> dict[str, Any]:
        """写入审计日志"""
        async with async_session() as db:
            audit_log = OperationAuditLog(
                session_id=session_id,
                user_id=user_id,
                workorder_id=workorder_id,
                operation_type=operation_type,
                is_risk=is_risk,
                operation_result=operation_result,
                create_time=datetime.now(),
                ip_address=ip_address,
            )
            db.add(audit_log)
            await db.commit()
            await db.refresh(audit_log)

            business_logger.info(
                "审计日志写入",
                session_id=session_id,
                user_id=user_id,
                workorder_id=workorder_id,
                operation_type=operation_type,
                is_risk=is_risk,
            )
            return {
                "id": audit_log.id,
                "session_id": audit_log.session_id,
                "operation_type": audit_log.operation_type,
                "is_risk": audit_log.is_risk,
                "operation_result": audit_log.operation_result,
                "create_time": audit_log.create_time.isoformat(),
            }

    async def query_audit_logs(
        self,
        workorder_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_risk: Optional[bool] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """查询审计日志"""
        async with async_session() as db:
            query = select(OperationAuditLog).order_by(OperationAuditLog.create_time.desc())

            if workorder_id:
                query = query.where(OperationAuditLog.workorder_id == workorder_id)
            if user_id:
                query = query.where(OperationAuditLog.user_id == user_id)
            if is_risk is not None:
                query = query.where(OperationAuditLog.is_risk == is_risk)

            query = query.limit(limit)
            result = await db.execute(query)
            logs = result.scalars().all()

            return [
                {
                    "id": log.id,
                    "session_id": log.session_id,
                    "user_id": log.user_id,
                    "workorder_id": log.workorder_id,
                    "operation_type": log.operation_type,
                    "is_risk": log.is_risk,
                    "operation_result": log.operation_result,
                    "create_time": log.create_time.isoformat(),
                    "ip_address": log.ip_address,
                }
                for log in logs
            ]


# 全局服务实例
audit_service = AuditService()
