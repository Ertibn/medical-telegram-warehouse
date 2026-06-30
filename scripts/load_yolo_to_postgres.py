"""
Load YOLO detection results from CSV to PostgreSQL.
"""

import csv
import logging
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_yolo_results(csv_path: str = "data/yolo_results.csv"):
    """Load YOLO results to PostgreSQL."""
    try:
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "5432"))
        db_name = os.getenv("DB_NAME", "telegram_warehouse")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")
        
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        with conn.cursor() as cur:
            # Create raw schema for image detections
            cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
            
            # Create table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS raw.image_detections (
                    id SERIAL PRIMARY KEY,
                    message_id INTEGER,
                    channel_name VARCHAR(255),
                    detected_class VARCHAR(255),
                    confidence_score FLOAT,
                    image_category VARCHAR(50),
                    num_objects INTEGER,
                    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            conn.commit()
            
            # Load data from CSV
            if not Path(csv_path).exists():
                logger.warning(f"CSV file not found: {csv_path}")
                return 0
            
            loaded_count = 0
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cur.execute("""
                        INSERT INTO raw.image_detections
                        (message_id, channel_name, detected_class, confidence_score,
                         image_category, num_objects)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        int(row['message_id']),
                        row['channel_name'],
                        row['detected_class'],
                        float(row['confidence_score']),
                        row['image_category'],
                        int(row['num_objects'])
                    ))
                    loaded_count += 1
            
            conn.commit()
            logger.info(f"Loaded {loaded_count} YOLO results to database")
            
            return loaded_count
        
    except Exception as e:
        logger.error(f"Error loading YOLO results: {e}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    load_yolo_results()
