from sqlalchemy import Boolean, Column, DateTime, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from crypto import decrypt

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(Text, nullable=False, unique=True)  # encrypted
    password_hash = Column(Text, nullable=False)  # bcrypt hash
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    categories = relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    transactions = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    cash_flow_template = relationship(
        "CashFlowTemplate",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    cash_flow_months = relationship(
        "CashFlowMonth", back_populates="user", cascade="all, delete-orphan"
    )

    def get_username(self):
        return decrypt(self.username)

    def to_json(self):
        return {
            "id": self.id,
            "username": self.get_username(),
            "is_admin": self.is_admin,
            "created_at": self.created_at,
        }
