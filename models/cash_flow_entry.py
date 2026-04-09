from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class CashFlowEntry(Base):
    """Entrada ou saída financeira dentro de um mês do fluxo de caixa."""

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

    __table_args__ = (Index("ix_cash_flow_entries_month_id", "month_id"),)

    month = relationship("CashFlowMonth", back_populates="entries")
