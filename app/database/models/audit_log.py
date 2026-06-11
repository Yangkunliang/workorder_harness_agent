"""
操作审计日志数据模型
"""
from datetime import datetime

from sqlalchemy import String, Boolean, BigInteger, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class OperationAuditLog(Base):
    """操作审计日志表"""
    __tablename__ = "operation_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, comment="会话ID")
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户ID")
    workorder_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="工单编号")
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="操作类型")
    is_risk: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否高危")
    operation_result: Mapped[str] = mapped_column(String(500), nullable=False, default="", comment="操作结果")
    create_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    ip_address: Mapped[str] = mapped_column(String(50), nullable=False, default="", comment="IP地址")
