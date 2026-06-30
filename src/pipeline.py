"""
Task 5: Pipeline Orchestration with Dagster
Orchestrates the entire ELT pipeline with proper dependency management.
"""

import logging
from datetime import datetime
from pathlib import Path

from dagster import (
    job, op, In, Out, DependencyDefinition,
    graph, Field, String, Int, Bool
)

logger = logging.getLogger(__name__)


@op(
    description="Extract data from Telegram channels",
    config_schema={
        "channels": Field(
            [String],
            default_value=["chemed_et", "lobeliacosmeticseth", "tikvahpharmaeth"],
            description="List of channels to scrape"
        ),
        "limit": Field(
            Int,
            default_value=1000,
            description="Messages per channel"
        )
    }
)
def scrape_telegram_data(context):
    """
    Extract messages from Telegram channels and populate data lake.
    """
    logger.info("Starting Telegram data extraction...")
    
    try:
        from scraper import TelegramScraper
        import asyncio
        import os
        
        # Load credentials
        api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        api_hash = os.getenv("TELEGRAM_API_HASH", "")
        phone = os.getenv("TELEGRAM_PHONE", "")
        
        if not all([api_id, api_hash, phone]):
            logger.warning("Telegram credentials not configured, using mock data generator")
            # Use mock data generator for testing
            from scripts.generate_mock_data import main as generate_mock
            generate_mock()
            return {
                "status": "completed",
                "method": "mock_data",
                "timestamp": datetime.now().isoformat()
            }
        
        channels = context.op_config.get("channels")
        limit = context.op_config.get("limit")
        
        scraper = TelegramScraper(api_id, api_hash, phone)
        
        async def run_scraper():
            if not await scraper.authenticate():
                return {"status": "failed", "error": "Authentication failed"}
            
            results = await scraper.scrape_multiple_channels(channels, limit)
            await scraper.close()
            return results
        
        results = asyncio.run(run_scraper())
        
        logger.info(f"Scraping completed: {results}")
        
        return {
            "status": "completed",
            "channels_scraped": len(channels),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in scrape_telegram_data: {e}")
        return {"status": "failed", "error": str(e)}


@op(
    description="Load raw JSON data to PostgreSQL",
    ins={"scrape_result": In()}
)
def load_raw_to_postgres(context, scrape_result):
    """
    Load scraped data from data lake to PostgreSQL raw schema.
    """
    logger.info("Starting data load to PostgreSQL...")
    
    try:
        from load_to_postgres import PostgresLoader
        import os
        
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "5432"))
        db_name = os.getenv("DB_NAME", "telegram_warehouse")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")
        
        loader = PostgresLoader(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        if not loader.connect():
            return {"status": "failed", "error": "Database connection failed"}
        
        loader.create_raw_schema()
        loader.load_from_data_lake()
        loader.verify_data()
        loader.close()
        
        logger.info("Data load completed successfully")
        
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in load_raw_to_postgres: {e}")
        return {"status": "failed", "error": str(e)}


@op(
    description="Run dbt transformations",
    ins={"load_result": In()}
)
def run_dbt_transformations(context, load_result):
    """
    Execute dbt run and test to transform raw data into dimensional model.
    """
    logger.info("Starting dbt transformations...")
    
    try:
        import subprocess
        import os
        
        # Change to dbt project directory
        dbt_dir = Path("medical_warehouse")
        
        if not dbt_dir.exists():
            logger.error("dbt project directory not found")
            return {"status": "failed", "error": "dbt project not found"}
        
        os.chdir(dbt_dir)
        
        # Run dbt parse
        logger.info("Running dbt parse...")
        result = subprocess.run(["dbt", "parse"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"dbt parse failed: {result.stderr}")
            return {"status": "failed", "error": "dbt parse failed"}
        
        # Run dbt run
        logger.info("Running dbt run...")
        result = subprocess.run(["dbt", "run"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"dbt run failed: {result.stderr}")
            return {"status": "failed", "error": "dbt run failed"}
        
        # Run dbt test
        logger.info("Running dbt test...")
        result = subprocess.run(["dbt", "test"], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"dbt test had failures: {result.stderr}")
        
        logger.info("dbt transformations completed")
        
        os.chdir("..")
        
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in run_dbt_transformations: {e}")
        return {"status": "failed", "error": str(e)}


@op(
    description="Run YOLO object detection on images",
    ins={"transform_result": In()}
)
def run_yolo_enrichment(context, transform_result):
    """
    Execute YOLO object detection on downloaded images.
    """
    logger.info("Starting YOLO enrichment...")
    
    try:
        from yolo_detect import YOLODetector
        
        detector = YOLODetector(model_name="yolov8n.pt")
        
        processed = detector.process_images_dir(
            images_dir="data/raw/images",
            output_csv="data/yolo_results.csv"
        )
        
        stats = detector.get_statistics("data/yolo_results.csv")
        
        logger.info(f"YOLO processing completed: {processed} images processed")
        logger.info(f"Statistics: {stats}")
        
        return {
            "status": "completed",
            "images_processed": processed,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error in run_yolo_enrichment: {e}")
        return {"status": "failed", "error": str(e)}


@graph
def medical_telegram_pipeline():
    """
    Complete ELT pipeline graph with all tasks.
    """
    scrape_result = scrape_telegram_data()
    load_result = load_raw_to_postgres(scrape_result=scrape_result)
    transform_result = run_dbt_transformations(load_result=load_result)
    yolo_result = run_yolo_enrichment(transform_result=transform_result)
    
    return yolo_result


@job(
    description="Medical Telegram Data Warehouse ELT Pipeline",
    tags={"team": "kara_solutions", "version": "1.0"}
)
def medical_warehouse_job():
    """Complete pipeline job."""
    return medical_telegram_pipeline()
