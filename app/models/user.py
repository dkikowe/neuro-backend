from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generation_count = Column(Integer, default=0, nullable=False)

    status = Column(String(64), default="active", nullable=False)
    email_verification_token_hash = Column(String(128), nullable=True)
    email_verification_expires_at = Column(DateTime, nullable=True)
    last_verification_sent_at = Column(DateTime, nullable=True)
    reset_token_hash = Column(String(128), nullable=True)
    reset_token_expires_at = Column(DateTime, nullable=True)

    uploads = relationship(
        "Upload",
        back_populates="user",
        cascade="all, delete-orphan",
    )


