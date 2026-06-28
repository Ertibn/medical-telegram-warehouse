"""
Load raw JSON data from data lake to PostgreSQL raw schema.
Creates raw.telegram_messages table and populates it from data lake.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/load_postgres.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PostgresLoader:
    """Loads data from data lake to PostgreSQL."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "telegram_warehouse",
        user: str = "postgres",
        password: str = ""
    ):
        """Initialize PostgreSQL connection."""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None

    def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Connected to PostgreSQL database: {self.database}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            return False

    def create_raw_schema(self):
        """Create raw schema and telegram_messages table."""
        try:
            with self.conn.cursor() as cur:
                # Create schema
                cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
                
                # Create table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                        id SERIAL PRIMARY KEY,
                        message_id INTEGER NOT NULL,
                        channel_name VARCHAR(255),
                        channel_username VARCHAR(255),
                        message_date TIMESTAMP,
                        message_text TEXT,
                        has_media BOOLEAN,
                        image_path VARCHAR(512),
                        views INTEGER DEFAULT 0,
                        forwards INTEGER DEFAULT 0,
                        media_type VARCHAR(100),
                        loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(message_id, channel_username)
                    );
                """)
                
                self.conn.commit()
                logger.info("Created raw schema and telegram_messages table")
        except Exception as e:
            logger.error(f"Error creating raw schema: {e}")
            self.conn.rollback()

    def load_from_data_lake(self, data_lake_path: str = "data/raw/telegram_messages"):
        """
        Load all JSON files from data lake to PostgreSQL.
        
        Args:
            data_lake_path: Path to partitioned data lake directory
        """
        try:
            data_path = Path(data_lake_path)
            
            if not data_path.exists():
                logger.error(f"Data lake path does not exist: {data_lake_path}")
                return
            
            total_records = 0
            
            # Iterate through date partitions
            for date_dir in sorted(data_path.iterdir()):
                if not date_dir.is_dir():
                    continue
                
                logger.info(f"Processing partition: {date_dir.name}")
                
                # Process each JSON file
                for json_file in date_dir.glob("*.json"):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            messages = json.load(f)
                        
                        if isinstance(messages, list):
                            inserted = self._insert_messages(messages)
                            total_records += inserted
                            logger.info(
                                f"Loaded {inserted} records from {json_file.name}"
                            )
                    except Exception as e:
                        logger.error(f"Error processing {json_file}: {e}")
                        continue
            
            logger.info(f"Completed loading. Total records: {total_records}")
        except Exception as e:
            logger.error(f"Error loading from data lake: {e}")

    def _insert_messages(self, messages: List[dict]) -> int:
        """
        Insert messages into PostgreSQL.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Number of records inserted
        """
        try:
            if not messages:
                return 0
            
            # Prepare data for insertion
            values = [
                (
                    msg.get('message_id'),
                    msg.get('channel_name'),
                    msg.get('channel_username'),
                    msg.get('message_date'),
                    msg.get('message_text'),
                    msg.get('has_media', False),
                    msg.get('image_path'),
                    msg.get('views', 0),
                    msg.get('forwards', 0),
                    msg.get('media_type')
                )
                for msg in messages
            ]
            
            with self.conn.cursor() as cur:
                # Use ON CONFLICT to handle duplicates
                execute_values(
                    cur,
                    """
                    INSERT INTO raw.telegram_messages 
                    (message_id, channel_name, channel_username, message_date, 
                     message_text, has_media, image_path, views, forwards, media_type)
                    VALUES %s
                    ON CONFLICT (message_id, channel_username) DO UPDATE
                    SET 
                        views = EXCLUDED.views,
                        forwards = EXCLUDED.forwards,
                        loaded_at = CURRENT_TIMESTAMP
                    """,
                    values
                )
            
            self.conn.commit()
            return len(values)
        except Exception as e:
            logger.error(f"Error inserting messages: {e}")
            self.conn.rollback()
            return 0

    def verify_data(self):
        """Verify loaded data quality."""
        try:
            with self.conn.cursor() as cur:
                # Get basic statistics
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_messages,
                        COUNT(DISTINCT channel_name) as num_channels,
                        COUNT(CASE WHEN has_media THEN 1 END) as messages_with_media,
                        COUNT(CASE WHEN image_path IS NOT NULL THEN 1 END) as with_images,
                        MIN(message_date) as earliest_message,
                        MAX(message_date) as latest_message
                    FROM raw.telegram_messages
                """)
                
                result = cur.fetchone()
                
                logger.info("=" * 60)
                logger.info("DATA QUALITY REPORT")
                logger.info("=" * 60)
                logger.info(f"Total messages: {result[0]}")
                logger.info(f"Unique channels: {result[1]}")
                logger.info(f"Messages with media: {result[2]}")
                logger.info(f"Messages with downloaded images: {result[3]}")
                logger.info(f"Earliest message: {result[4]}")
                logger.info(f"Latest message: {result[5]}")
                logger.info("=" * 60)
                
        except Exception as e:
            logger.error(f"Error verifying data: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from PostgreSQL")


def main():
    """Main entry point."""
    # Load config from environment
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = int(os.getenv("DB_PORT", "5432"))
    db_name = os.getenv("DB_NAME", "telegram_warehouse")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")
    
    # Initialize loader
    loader = PostgresLoader(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    
    try:
        # Connect and setup
        if not loader.connect():
            return
        
        loader.create_raw_schema()
        
        # Load data
        loader.load_from_data_lake()
        
        # Verify
        loader.verify_data()
        
    finally:
        loader.close()


if __name__ == "__main__":
    main()
