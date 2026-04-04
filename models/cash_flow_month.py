from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class CashFlowMonth(Base):
    """Representa um mês financeiro de um usuário no fluxo de caixa."""

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
