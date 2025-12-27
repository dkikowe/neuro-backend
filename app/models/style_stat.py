from sqlalchemy import Column, Integer, String

from app.core.database import Base


class StyleStat(Base):
    __tablename__ = "style_stats"

    style_id = Column(String(64), primary_key=True, index=True)
    count = Column(Integer, nullable=False, default=0)

