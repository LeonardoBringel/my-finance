from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    category_id = Column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    date = Column(Text, nullable=False)  # encrypted
    description = Column(Text, nullable=True)  # encrypted
    value = Column(Text, nullable=False)  # encrypted float as string
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

    user = relationship("User", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")

    def to_json(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "date": decrypt(self.date),
            "description": decrypt(self.description),
            "value": decrypt_float(self.value),
            "installment_group": self.installment_group,
            "installment_number": self.installment_number,
            "installment_total": self.installment_total,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
