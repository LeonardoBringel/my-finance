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


class CashFlowTemplateItem(Base):
    """Linha de lançamento recorrente dentro de um template de fluxo de caixa."""

    __tablename__ = "cash_flow_template_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(
        Integer,
        ForeignKey("cash_flow_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(Text, nullable=False)
    day = Column(Integer, nullable=False)  # dia do mês (1-31)
    value = Column(Numeric(12, 2), nullable=False)
    type = Column(String(10), nullable=False)  # 'entrada' | 'saida'
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    template = relationship("CashFlowTemplate", back_populates="items")
