from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class CashFlowTemplate(Base):
    """One template per user — defines recurring items copied to new months."""

    __tablename__ = "cash_flow_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="cash_flow_template")
    items = relationship(
        "CashFlowTemplateItem", back_populates="template", cascade="all, delete-orphan"
    )


class CashFlowTemplateItem(Base):
    """A single recurring line in the template."""

    __tablename__ = "cash_flow_template_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(
        Integer,
        ForeignKey("cash_flow_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(Text, nullable=False)
    day = Column(Integer, nullable=False)  # day of month (1-31)
    value = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10), nullable=False)  # 'entrada' | 'saida'
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    template = relationship("CashFlowTemplate", back_populates="items")


class CashFlowMonth(Base):
    """A financial month owned by a user."""

    __tablename__ = "cash_flow_months"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="cash_flow_months")
    entries = relationship(
        "CashFlowEntry", back_populates="month", cascade="all, delete-orphan"
    )


class CashFlowEntry(Base):
    """A single income/expense entry within a cash flow month."""

    __tablename__ = "cash_flow_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    month_id = Column(
        Integer, ForeignKey("cash_flow_months.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(Text, nullable=False)
    day = Column(Integer, nullable=False)
    value = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10), nullable=False)  # 'entrada' | 'saida'
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    month = relationship("CashFlowMonth", back_populates="entries")
