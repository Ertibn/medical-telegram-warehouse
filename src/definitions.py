"""
Dagster definitions and deployment configuration.
"""

from dagster import define_asset_job, DefaultSensorDefinition, build_schedule_context
from dagster_cron import cron_schedule

from pipeline import medical_warehouse_job

# Define a daily schedule for the pipeline
daily_medical_warehouse_job = medical_warehouse_job.to_job(
    name="daily_medical_warehouse_pipeline",
    tags={"schedule": "daily"}
)
