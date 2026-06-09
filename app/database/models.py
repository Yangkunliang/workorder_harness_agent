"""
MySQL 数据表模型
- 工单主表 workorder
- 操作审计日志表 operation_audit_log
"""
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean, Integer, BigInteger, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class Workorder(Base):
    """工单主表"""
    __tablename__ = "workorder"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    workorder_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True, comment="工单编号")
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="工单标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="工单内容")
    create_user: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment="创建人")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="正常", comment="工单状态：正常/已关闭/已删除")
    create_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="软删除标记")

    __table_args__ = (
        Index("idx_workorder_status", "status"),
        Index("idx_workorder_create_user", "create_user"),
    )


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
