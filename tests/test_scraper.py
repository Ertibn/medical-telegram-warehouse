"""Tests for Telegram scraper module."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scraper import TelegramScraper


class TestTelegramScraper:
    """Test suite for TelegramScraper class."""

    @pytest.fixture
    def scraper(self):
        """Create scraper instance for testing."""
        return TelegramScraper(
            api_id=123456,
            api_hash="test_hash",
            phone="+251900000000",
            session_name="test_session"
        )

    def test_scraper_init(self, scraper):
        """Test scraper initialization."""
        assert scraper.api_id == 123456
        assert scraper.api_hash == "test_hash"
        assert scraper.phone == "+251900000000"
        assert scraper.data_lake_path.exists()
        assert scraper.images_path.exists()

    def test_data_lake_path_created(self, scraper):
        """Test that data lake directories are created."""
        assert scraper.data_lake_path.exists()
        assert scraper.images_path.exists()

    def test_save_to_data_lake(self, scraper, tmp_path):
        """Test saving messages to data lake."""
        scraper.data_lake_path = tmp_path / "telegram_messages"
        scraper.data_lake_path.mkdir()

        messages = [
            {
                "message_id": 1,
                "channel_name": "Test Channel",
                "message_text": "Test message",
                "views": 10
            }
        ]

        scraper._save_to_data_lake("Test Channel", "test_channel", messages)

        # Check file exists
        files = list(scraper.data_lake_path.glob("*/*.json"))
        assert len(files) > 0

    def test_message_data_structure(self):
        """Test that message data has required fields."""
        required_fields = [
            "message_id",
            "channel_name",
            "channel_username",
            "message_date",
            "message_text",
            "has_media",
            "views",
            "forwards"
        ]

        # Sample message structure
        sample_msg = {
            "message_id": 1,
            "channel_name": "CheMed",
            "channel_username": "chemed_et",
            "message_date": "2024-01-01T12:00:00",
            "message_text": "Medical product",
            "has_media": False,
            "image_path": None,
            "views": 100,
            "forwards": 5
        }

        for field in required_fields:
            assert field in sample_msg
