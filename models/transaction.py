from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from utils.crypto import decrypt, decrypt_float

from .base import Base


class Transaction(Base):
    """Representa uma transação financeira (entrada ou saída) de um usuário."""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    date = Column(Text, nullable=False)  # criptografado
    year = Column(
        Integer, nullable=True
    )  # ano da transação em texto plano, para filtros SQL
    description = Column(Text, nullable=True)  # criptografado
    value = Column(Text, nullable=False)  # float criptografado como string
    installment_group = Column(Text, nullable=True)
    installment_number = Column(Integer, nullable=True)
    installment_total = Column(Integer, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (Index("ix_transactions_user_year", "user_id", "year"),)

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

    def to_json(self) -> dict:
        """Serializa a transação para um dicionário com os campos descriptografados."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "date": decrypt(self.date),
            "year": self.year,
            "description": decrypt(self.description),
            "value": decrypt_float(self.value),
            "installment_group": self.installment_group,
            "installment_number": self.installment_number,
            "installment_total": self.installment_total,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
