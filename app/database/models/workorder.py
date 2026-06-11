"""
工单数据模型
"""
from datetime import datetime

from sqlalchemy import String, Text, DateTime, Boolean, BigInteger, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class Workorder(Base):
    """工单主表"""
    __tablename__ = "workorder"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    workorder_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True, comment="工单编号")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="工单标题")
    status: Mapped[str] = mapped_column(String(32), nullable=False, comment="工单状态：pending/processing/completed/cancelled")
    creator: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="创建人")
    description: Mapped[str] = mapped_column(Text, nullable=True, comment="工单描述")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="软删除标记")

    __table_args__ = (
        Index("idx_workorder_no", "workorder_no", unique=True),
        Index("idx_workorder_creator", "creator"),
        Index("idx_workorder_created_at", "created_at"),
        Index("idx_workorder_status", "status"),
    )

    # 兼容旧字段名
    @property
    def workorder_id(self):
        return self.workorder_no

    @property
    def content(self):
        return self.description

    @property
    def create_user(self):
        return self.creator

    @property
    def create_time(self):
        return self.created_at

    @property
    def update_time(self):
        return self.updated_at
