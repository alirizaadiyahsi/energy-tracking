import logging
from datetime import datetime, timedelta
from typing import List, Optional

from core.database import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from models.energy_metrics import EnergyMetrics
from models.processing_job import ProcessingJob
from schemas.processing import (EnergyMetricsResponse, ProcessingJobCreate,
                                ProcessingJobResponse, ProcessingStatsResponse)
from services.influx_service import InfluxService
from services.processing_service import ProcessingService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
processing_service = ProcessingService()
influx_service = InfluxService()


@router.get("/jobs", response_model=List[ProcessingJobResponse])
async def get_processing_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get processing jobs with optional filtering"""
    try:
        query = select(ProcessingJob)

        if status:
            query = query.where(ProcessingJob.status == status)
        if job_type:
            query = query.where(ProcessingJob.job_type == job_type)

        query = (
            query.order_by(ProcessingJob.created_at.desc()).limit(limit).offset(offset)
        )
        result = await db.execute(query)
        jobs = result.scalars().all()

        return [ProcessingJobResponse.from_orm(job) for job in jobs]
    except Exception as e:
        logger.error(f"Error getting processing jobs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/jobs", response_model=ProcessingJobResponse)
async def create_processing_job(
    job_data: ProcessingJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new processing job"""
    try:
        # Create job in database
        db_job = ProcessingJob(
            job_type=job_data.job_type,
            parameters=job_data.parameters,
            created_by=job_data.created_by,
        )
        db.add(db_job)
        await db.commit()
        await db.refresh(db_job)

        # Schedule background processing
        if job_data.job_type == "aggregation":
            background_tasks.add_task(
                processing_service.process_energy_aggregation, db_job.id
            )
        elif job_data.job_type == "anomaly_detection":
            background_tasks.add_task(processing_service.detect_anomalies, db_job.id)
        elif job_data.job_type == "cleanup":
            background_tasks.add_task(processing_service.cleanup_old_data, db_job.id)

        return ProcessingJobResponse.from_orm(db_job)
    except Exception as e:
        logger.error(f"Error creating processing job: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
async def get_processing_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific processing job by ID"""
    try:
        query = select(ProcessingJob).where(ProcessingJob.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail="Processing job not found")

        return ProcessingJobResponse.from_orm(job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/metrics", response_model=List[EnergyMetricsResponse])
async def get_energy_metrics(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get energy metrics with optional filtering"""
    try:
        query = select(EnergyMetrics)

        if device_id:
            query = query.where(EnergyMetrics.device_id == device_id)
        if metric_type:
            query = query.where(EnergyMetrics.metric_type == metric_type)
        if start_date:
            query = query.where(EnergyMetrics.period_start >= start_date)
        if end_date:
            query = query.where(EnergyMetrics.period_end <= end_date)

        query = (
            query.order_by(EnergyMetrics.period_start.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        metrics = result.scalars().all()

        return [EnergyMetricsResponse.from_orm(metric) for metric in metrics]
    except Exception as e:
        logger.error(f"Error getting energy metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/aggregate")
async def trigger_aggregation(
    background_tasks: BackgroundTasks,
    device_id: Optional[str] = Query(None, description="Device ID to aggregate"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for aggregation"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for aggregation"),
):
    """Trigger energy data aggregation"""
    try:
        # Create processing job
        job_data = ProcessingJobCreate(
            job_type="aggregation",
            parameters={
                "device_id": device_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        )

        # This would normally go through the create_processing_job endpoint
        # For simplicity, we'll trigger the background task directly
        background_tasks.add_task(
            processing_service.process_energy_aggregation, job_data.parameters
        )

        return {"message": "Aggregation job queued successfully"}
    except Exception as e:
        logger.error(f"Error triggering aggregation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=ProcessingStatsResponse)
async def get_processing_stats(db: AsyncSession = Depends(get_db)):
    """Get processing statistics"""
    try:
        # Get job statistics
        total_jobs_query = select(ProcessingJob)
        total_jobs_result = await db.execute(total_jobs_query)
        total_jobs = len(total_jobs_result.scalars().all())

        pending_jobs_query = select(ProcessingJob).where(
            ProcessingJob.status == "pending"
        )
        pending_jobs_result = await db.execute(pending_jobs_query)
        pending_jobs = len(pending_jobs_result.scalars().all())

        completed_jobs_query = select(ProcessingJob).where(
            ProcessingJob.status == "completed"
        )
        completed_jobs_result = await db.execute(completed_jobs_query)
        completed_jobs = len(completed_jobs_result.scalars().all())

        failed_jobs_query = select(ProcessingJob).where(
            ProcessingJob.status == "failed"
        )
        failed_jobs_result = await db.execute(failed_jobs_query)
        failed_jobs = len(failed_jobs_result.scalars().all())

        # Get metrics statistics
        total_metrics_query = select(EnergyMetrics)
        total_metrics_result = await db.execute(total_metrics_query)
        total_metrics = len(total_metrics_result.scalars().all())

        return ProcessingStatsResponse(
            total_jobs=total_jobs,
            pending_jobs=pending_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            total_metrics=total_metrics,
        )
    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
