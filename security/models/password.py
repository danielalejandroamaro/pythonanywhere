from sqlalchemy.orm import relationship
from sqlalchemy.schema import Column, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import String, Integer, DateTime

from config import PRIMARY_KEY_USER

from engine import Base


class UserPassword(Base):
    __tablename__ = 'user_password'
    pasword_hash = Column(String(60))
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=False), onupdate=func.now())

    # region  relationship

    user_id = Column(Integer, ForeignKey(PRIMARY_KEY_USER, ondelete="CASCADE"), primary_key=True, nullable=False)
    user = relationship("User", back_populates="password")

    # endregion  relationship
