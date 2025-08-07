from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class ProcessingJobCreate(BaseModel):
    job_type: str
    parameters: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None


class ProcessingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    status: str
    parameters: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[str]


class EnergyMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    metric_type: str
    period_start: datetime
    period_end: datetime
    total_energy: float
    avg_power: float
    max_power: float
    min_power: float
    energy_cost: float
    efficiency_score: Optional[float]
    anomaly_detected: bool
    anomaly_score: Optional[float]
    data_points_count: int
    created_at: datetime
    updated_at: Optional[datetime]


class ProcessingStatsResponse(BaseModel):
    total_jobs: int
    pending_jobs: int
    completed_jobs: int
    failed_jobs: int
    total_metrics: int
