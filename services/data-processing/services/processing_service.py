import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.config import settings
from models.processing_job import ProcessingJob
from models.energy_metrics import EnergyMetrics
from services.influx_service import InfluxService

logger = logging.getLogger(__name__)

class ProcessingService:
    def __init__(self):
        self.influx_service = InfluxService()
    
    async def process_energy_aggregation(self, job_id_or_params):
        """Process energy data aggregation"""
        logger.info(f"Starting energy aggregation processing: {job_id_or_params}")
        
        async with AsyncSessionLocal() as db:
            try:
                # Handle both job_id (int) and parameters (dict)
                if isinstance(job_id_or_params, int):
                    job_id = job_id_or_params
                    job = await self._get_job(db, job_id)
                    if not job:
                        return
                    
                    # Update job status
                    job.status = "running"
                    job.started_at = datetime.utcnow()
                    await db.commit()
                    
                    params = job.parameters or {}
                else:
                    params = job_id_or_params
                    job = None
                
                # Extract parameters
                device_id = params.get("device_id")
                start_date = params.get("start_date")
                end_date = params.get("end_date")
                
                if start_date:
                    start_date = datetime.fromisoformat(start_date)
                else:
                    start_date = datetime.utcnow() - timedelta(days=1)
                    
                if end_date:
                    end_date = datetime.fromisoformat(end_date)
                else:
                    end_date = datetime.utcnow()
                
                # Get raw energy data from InfluxDB
                raw_data = await self.influx_service.get_energy_data(
                    device_id=device_id,
                    start_time=start_date,
                    end_time=end_date
                )
                
                if not raw_data:
                    logger.warning(f"No data found for aggregation: {params}")
                    if job:
                        job.status = "completed"
                        job.completed_at = datetime.utcnow()
                        job.result = {"message": "No data to aggregate"}
                        await db.commit()
                    return
                
                # Process aggregations for different time periods
                aggregations = []
                for period_type in ["hourly", "daily"]:
                    period_data = self._aggregate_by_period(raw_data, period_type)
                    
                    for period_item in period_data:
                        # Create or update energy metrics
                        metrics = EnergyMetrics(
                            device_id=period_item["device_id"],
                            metric_type=period_type,
                            period_start=period_item["period_start"],
                            period_end=period_item["period_end"],
                            total_energy=period_item["total_energy"],
                            avg_power=period_item["avg_power"],
                            max_power=period_item["max_power"],
                            min_power=period_item["min_power"],
                            energy_cost=period_item["energy_cost"],
                            data_points_count=period_item["data_points_count"]
                        )
                        
                        # Check if metrics already exist for this period
                        existing = await db.execute(
                            select(EnergyMetrics).where(
                                and_(
                                    EnergyMetrics.device_id == metrics.device_id,
                                    EnergyMetrics.metric_type == metrics.metric_type,
                                    EnergyMetrics.period_start == metrics.period_start
                                )
                            )
                        )
                        existing_metric = existing.scalar_one_or_none()
                        
                        if existing_metric:
                            # Update existing metric
                            for key, value in period_item.items():
                                if hasattr(existing_metric, key):
                                    setattr(existing_metric, key, value)
                            existing_metric.updated_at = datetime.utcnow()
                        else:
                            # Add new metric
                            db.add(metrics)
                            aggregations.append(period_item)
                
                await db.commit()
                
                if job:
                    job.status = "completed"
                    job.completed_at = datetime.utcnow()
                    job.result = {
                        "aggregations_created": len(aggregations),
                        "processed_records": len(raw_data)
                    }
                    await db.commit()
                
                logger.info(f"Energy aggregation completed. Created {len(aggregations)} aggregations")
                
            except Exception as e:
                logger.error(f"Error in energy aggregation: {e}")
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    await db.commit()
    
    async def detect_anomalies(self, job_id):
        """Detect anomalies in energy consumption"""
        logger.info(f"Starting anomaly detection for job {job_id}")
        
        async with AsyncSessionLocal() as db:
            try:
                job = await self._get_job(db, job_id)
                if not job:
                    return
                
                # Update job status
                job.status = "running"
                job.started_at = datetime.utcnow()
                await db.commit()
                
                # Get recent energy metrics
                recent_metrics = await db.execute(
                    select(EnergyMetrics).where(
                        EnergyMetrics.period_start >= datetime.utcnow() - timedelta(days=30)
                    ).order_by(EnergyMetrics.period_start.desc())
                )
                metrics = recent_metrics.scalars().all()
                
                if len(metrics) < 10:
                    logger.warning("Not enough data for anomaly detection")
                    job.status = "completed"
                    job.completed_at = datetime.utcnow()
                    job.result = {"message": "Insufficient data for anomaly detection"}
                    await db.commit()
                    return
                
                # Prepare data for anomaly detection
                df = pd.DataFrame([
                    {
                        'device_id': m.device_id,
                        'total_energy': m.total_energy,
                        'avg_power': m.avg_power,
                        'max_power': m.max_power,
                        'period_start': m.period_start
                    }
                    for m in metrics
                ])
                
                anomalies_detected = 0
                
                # Group by device for device-specific anomaly detection
                for device_id, device_data in df.groupby('device_id'):
                    if len(device_data) < 5:
                        continue
                    
                    # Use Isolation Forest for anomaly detection
                    features = device_data[['total_energy', 'avg_power', 'max_power']].values
                    
                    # Handle any NaN values
                    features = np.nan_to_num(features)
                    
                    iso_forest = IsolationForest(
                        contamination=0.1,  # Expect 10% anomalies
                        random_state=42
                    )
                    
                    anomaly_labels = iso_forest.fit_predict(features)
                    anomaly_scores = iso_forest.score_samples(features)
                    
                    # Update metrics with anomaly information
                    for idx, (metric_idx, row) in enumerate(device_data.iterrows()):
                        is_anomaly = anomaly_labels[idx] == -1
                        anomaly_score = abs(anomaly_scores[idx])
                        
                        # Find corresponding metric in database
                        for metric in metrics:
                            if (metric.device_id == device_id and 
                                metric.period_start == row['period_start']):
                                metric.anomaly_detected = is_anomaly
                                metric.anomaly_score = float(anomaly_score)
                                if is_anomaly:
                                    anomalies_detected += 1
                                break
                
                await db.commit()
                
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.result = {
                    "anomalies_detected": anomalies_detected,
                    "total_metrics_analyzed": len(metrics)
                }
                await db.commit()
                
                logger.info(f"Anomaly detection completed. Found {anomalies_detected} anomalies")
                
            except Exception as e:
                logger.error(f"Error in anomaly detection: {e}")
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                await db.commit()
    
    async def cleanup_old_data(self, job_id):
        """Clean up old processed data"""
        logger.info(f"Starting data cleanup for job {job_id}")
        
        async with AsyncSessionLocal() as db:
            try:
                job = await self._get_job(db, job_id)
                if not job:
                    return
                
                # Update job status
                job.status = "running"
                job.started_at = datetime.utcnow()
                await db.commit()
                
                # Clean up old completed jobs (older than 30 days)
                old_jobs_cutoff = datetime.utcnow() - timedelta(days=30)
                old_jobs = await db.execute(
                    select(ProcessingJob).where(
                        and_(
                            ProcessingJob.status == "completed",
                            ProcessingJob.completed_at < old_jobs_cutoff
                        )
                    )
                )
                jobs_to_delete = old_jobs.scalars().all()
                
                deleted_jobs = 0
                for old_job in jobs_to_delete:
                    await db.delete(old_job)
                    deleted_jobs += 1
                
                # Clean up old energy metrics (older than 1 year)
                old_metrics_cutoff = datetime.utcnow() - timedelta(days=365)
                old_metrics = await db.execute(
                    select(EnergyMetrics).where(
                        EnergyMetrics.period_start < old_metrics_cutoff
                    )
                )
                metrics_to_delete = old_metrics.scalars().all()
                
                deleted_metrics = 0
                for old_metric in metrics_to_delete:
                    await db.delete(old_metric)
                    deleted_metrics += 1
                
                await db.commit()
                
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.result = {
                    "deleted_jobs": deleted_jobs,
                    "deleted_metrics": deleted_metrics
                }
                await db.commit()
                
                logger.info(f"Data cleanup completed. Deleted {deleted_jobs} jobs and {deleted_metrics} metrics")
                
            except Exception as e:
                logger.error(f"Error in data cleanup: {e}")
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                await db.commit()
    
    def _aggregate_by_period(self, raw_data: List[Dict], period_type: str) -> List[Dict]:
        """Aggregate raw energy data by time period"""
        if not raw_data:
            return []
        
        df = pd.DataFrame(raw_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Set aggregation frequency
        freq = 'H' if period_type == 'hourly' else 'D'
        
        aggregated_data = []
        
        for device_id, device_data in df.groupby('device_id'):
            # Resample data by period
            device_data = device_data.set_index('timestamp')
            resampled = device_data.resample(freq).agg({
                'power': ['mean', 'max', 'min'],
                'energy': 'sum'
            }).dropna()
            
            for period_start, row in resampled.iterrows():
                period_end = period_start + pd.Timedelta(hours=1 if period_type == 'hourly' else 24)
                
                total_energy = float(row[('energy', 'sum')])
                avg_power = float(row[('power', 'mean')])
                max_power = float(row[('power', 'max')])
                min_power = float(row[('power', 'min')])
                
                # Simple cost calculation (would use actual tariff rates)
                energy_cost = total_energy * 0.15  # $0.15 per kWh
                
                aggregated_data.append({
                    'device_id': device_id,
                    'period_start': period_start.to_pydatetime(),
                    'period_end': period_end.to_pydatetime(),
                    'total_energy': total_energy,
                    'avg_power': avg_power,
                    'max_power': max_power,
                    'min_power': min_power,
                    'energy_cost': energy_cost,
                    'data_points_count': len(device_data)
                })
        
        return aggregated_data
    
    async def _get_job(self, db: AsyncSession, job_id: int) -> Optional[ProcessingJob]:
        """Get processing job by ID"""
        try:
            result = await db.execute(
                select(ProcessingJob).where(ProcessingJob.id == job_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
