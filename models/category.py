from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from crypto import decrypt

from .base import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(Text, nullable=False)  # encrypted
    type = Column(Text, nullable=False)  # encrypted ('entrada'|'saida'|'ambos')
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

    def get_name(self):
        return decrypt(self.name)

    def get_type(self):
        return decrypt(self.type)

    def to_json(self):
        return {
            "id": self.id,
            "name": self.get_name(),
            "type": self.get_type(),
        }
