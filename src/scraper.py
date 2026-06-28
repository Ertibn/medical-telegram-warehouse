"""
Task 1: Telegram Data Scraper
Extracts messages and images from public Telegram channels.
Stores raw data in a data lake with partitioned directory structure.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramScraper:
    """Scrapes Telegram channels and stores data in a data lake."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        session_name: str = "scraper_session"
    ):
        """
        Initialize the Telegram scraper.

        Args:
            api_id: Telegram API ID from my.telegram.org
            api_hash: Telegram API hash from my.telegram.org
            phone: Phone number associated with Telegram account
            session_name: Session file name for persistent login
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_name = session_name
        self.client = TelegramClient(session_name, api_id, api_hash)
        
        # Create data lake directories
        self.data_lake_path = Path("data/raw/telegram_messages")
        self.images_path = Path("data/raw/images")
        self.data_lake_path.mkdir(parents=True, exist_ok=True)
        self.images_path.mkdir(parents=True, exist_ok=True)

    async def authenticate(self) -> bool:
        """Authenticate with Telegram API."""
        try:
            logger.info("Connecting to Telegram API...")
            await self.client.connect()

            if not await self.client.is_user_authorized():
                logger.info("Requesting code from Telegram...")
                await self.client.send_code_request(self.phone)
                code = input("Enter the code: ")

                try:
                    await self.client.sign_in(self.phone, code)
                except SessionPasswordNeededError:
                    password = input("Enter your password: ")
                    await self.client.sign_in(password=password)

            logger.info("Successfully authenticated with Telegram")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    async def scrape_channel(
        self,
        channel_username: str,
        limit: int = 1000
    ) -> Dict[str, any]:
        """
        Scrape messages from a Telegram channel.

        Args:
            channel_username: Channel username (without @)
            limit: Number of messages to retrieve

        Returns:
            Dictionary with scraping statistics
        """
        try:
            logger.info(f"Starting to scrape channel: {channel_username}")
            
            # Get channel entity
            channel = await self.client.get_entity(channel_username)
            channel_name = channel.title or channel_username
            
            messages_data = []
            image_count = 0
            error_count = 0
            
            # Get messages from channel
            async for message in self.client.iter_messages(channel, limit=limit):
                try:
                    # Extract message data
                    msg_dict = {
                        "message_id": message.id,
                        "channel_name": channel_name,
                        "channel_username": channel_username,
                        "message_date": message.date.isoformat() if message.date else None,
                        "message_text": message.text or "",
                        "has_media": bool(message.media),
                        "image_path": None,
                        "views": message.views or 0,
                        "forwards": message.forwards or 0,
                        "media_type": type(message.media).__name__ if message.media else None
                    }
                    
                    # Download image if present
                    if message.photo:
                        try:
                            image_filename = await self._download_image(
                                message, channel_name
                            )
                            msg_dict["image_path"] = image_filename
                            image_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to download image for msg {message.id}: {e}")
                    
                    messages_data.append(msg_dict)
                    
                except Exception as e:
                    logger.warning(f"Error processing message {message.id}: {e}")
                    error_count += 1
                    continue
            
            # Save messages to data lake
            if messages_data:
                self._save_to_data_lake(channel_name, channel_username, messages_data)
            
            stats = {
                "channel": channel_name,
                "messages_scraped": len(messages_data),
                "images_downloaded": image_count,
                "errors": error_count,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Completed scraping {channel_name}: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error scraping channel {channel_username}: {e}")
            return {"channel": channel_username, "error": str(e)}

    async def _download_image(self, message, channel_name: str) -> Optional[str]:
        """Download image from message."""
        try:
            channel_dir = self.images_path / channel_name
            channel_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{message.id}.jpg"
            filepath = channel_dir / filename
            
            await self.client.download_media(message, file=filepath)
            
            return f"data/raw/images/{channel_name}/{filename}"
        except Exception as e:
            logger.error(f"Failed to download image: {e}")
            return None

    def _save_to_data_lake(
        self,
        channel_name: str,
        channel_username: str,
        messages: List[Dict]
    ):
        """Save messages to partitioned data lake."""
        try:
            # Use today's date for partitioning
            today = datetime.now().strftime("%Y-%m-%d")
            partition_dir = self.data_lake_path / today
            partition_dir.mkdir(parents=True, exist_ok=True)
            
            # Save as JSON
            filename = f"{channel_username}.json"
            filepath = partition_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(messages)} messages to {filepath}")
        except Exception as e:
            logger.error(f"Error saving to data lake: {e}")

    async def scrape_multiple_channels(
        self,
        channels: List[str],
        limit: int = 1000
    ) -> List[Dict]:
        """
        Scrape multiple channels sequentially.

        Args:
            channels: List of channel usernames
            limit: Messages per channel

        Returns:
            List of scraping statistics
        """
        results = []
        for channel in channels:
            result = await self.scrape_channel(channel, limit)
            results.append(result)
            # Add delay to avoid rate limiting
            await asyncio.sleep(2)
        
        return results

    async def close(self):
        """Close Telegram client connection."""
        await self.client.disconnect()
        logger.info("Disconnected from Telegram API")


async def main():
    """Main entry point for scraper."""
    # Load credentials from environment
    api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    phone = os.getenv("TELEGRAM_PHONE", "")
    
    if not all([api_id, api_hash, phone]):
        logger.error("Missing Telegram credentials in .env file")
        return
    
    # Channels to scrape
    channels = [
        "chemed_et",  # CheMed Telegram Channel
        "lobeliacosmeticsEthiopia",  # Lobelia Cosmetics
        "TikvahPharmEthiopia"  # Tikvah Pharma
    ]
    
    scraper = TelegramScraper(api_id, api_hash, phone)
    
    try:
        # Authenticate
        if not await scraper.authenticate():
            return
        
        # Scrape channels
        results = await scraper.scrape_multiple_channels(channels, limit=1000)
        
        # Log summary
        logger.info("=" * 60)
        logger.info("SCRAPING SUMMARY")
        logger.info("=" * 60)
        for result in results:
            if "error" not in result:
                logger.info(
                    f"{result['channel']}: {result['messages_scraped']} messages, "
                    f"{result['images_downloaded']} images"
                )
            else:
                logger.error(f"{result['channel']}: {result['error']}")
        
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
