from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("inv_id", name="uq_payments_inv_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    inv_id = Column(Integer, nullable=False, index=True)  # InvId from Robokassa
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(String(64), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(512), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)

