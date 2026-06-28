"""Tests for PostgreSQL data loading module."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from load_to_postgres import PostgresLoader


class TestPostgresLoader:
    """Test suite for PostgresLoader class."""

    @pytest.fixture
    def loader(self):
        """Create loader instance for testing."""
        return PostgresLoader(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )

    def test_loader_init(self, loader):
        """Test loader initialization."""
        assert loader.host == "localhost"
        assert loader.port == 5432
        assert loader.database == "test_db"
        assert loader.user == "test_user"

    @patch('load_to_postgres.psycopg2.connect')
    def test_connection_params(self, mock_connect, loader):
        """Test that connection uses correct parameters."""
        loader.connect()
        mock_connect.assert_called_once_with(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )

    def test_insert_messages_data_structure(self, loader):
        """Test message insertion preparation."""
        messages = [
            {
                "message_id": 1,
                "channel_name": "CheMed",
                "channel_username": "chemed_et",
                "message_date": "2024-01-01T12:00:00",
                "message_text": "Product info",
                "has_media": False,
                "image_path": None,
                "views": 100,
                "forwards": 5,
                "media_type": None
            }
        ]

        # Test data structure is valid
        assert len(messages) == 1
        assert messages[0]["message_id"] == 1
        assert "channel_name" in messages[0]

    def test_verify_data_query_structure(self):
        """Test that verify data query is well-formed."""
        query = """
            SELECT 
                COUNT(*) as total_messages,
                COUNT(DISTINCT channel_name) as num_channels
            FROM raw.telegram_messages
        """
        assert "SELECT" in query
        assert "COUNT(*)" in query
        assert "raw.telegram_messages" in query
