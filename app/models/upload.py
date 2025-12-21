from datetime import datetime

from datetime import timedelta, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    before_url = Column(String(512), nullable=False)
    after_url = Column(String(512), nullable=True)
    style = Column(String(64), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    days_left = Column(Integer, nullable=True)

    user = relationship("User", back_populates="uploads")

    def set_expiry(self, days: int = 30) -> None:
        self.expires_at = (self.created_at or datetime.utcnow()) + timedelta(days=days)
        self.days_left = days

