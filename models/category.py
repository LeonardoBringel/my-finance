from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from utils.crypto import decrypt

from .base import Base


class Category(Base):
    """Representa uma categoria de transação pertencente a um usuário."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(Text, nullable=False)  # criptografado
    type = Column(Text, nullable=False)  # criptografado ('entrada'|'saida'|'ambos')
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="categories")
    transactions = relationship("Transaction", back_populates="category")

    def get_name(self) -> str:
        """Descriptografa e retorna o nome da categoria."""
        return decrypt(self.name)

    def get_type(self) -> str:
        """Descriptografa e retorna o tipo da categoria."""
        return decrypt(self.type)

    def to_json(self) -> dict:
        """Serializa a categoria para um dicionário."""
        return {
            "id": self.id,
            "name": self.get_name(),
            "type": self.get_type(),
        }
