from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class CashFlowTemplate(Base):
    """Template de lançamentos recorrentes pertencente a um usuário.

    Define os itens padrão que são copiados automaticamente ao criar novos meses
    no fluxo de caixa.
    """

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
