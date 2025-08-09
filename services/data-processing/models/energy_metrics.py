from core.database import Base
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func


class EnergyMetrics(Base):
    __tablename__ = "energy_metrics"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    location = Column(String(100))
    device_metadata = Column(Text)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    quality_score = Column(Float, default=1.0)
