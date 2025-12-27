from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.core.database import Base


class GenerationBalance(Base):
    __tablename__ = "generations"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_generations_user_id"),
        UniqueConstraint("email", name="uq_generations_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    remaining_std = Column(Integer, nullable=False, default=1)
    used_std = Column(Integer, nullable=False, default=0)
    remaining_hd = Column(Integer, nullable=False, default=0)
    used_hd = Column(Integer, nullable=False, default=0)
    current_plan = Column(String(64), nullable=False, default="free")  # только подписка
    package_plan_id = Column(String(64), nullable=True)  # последний разовый пакет
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    plan_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

