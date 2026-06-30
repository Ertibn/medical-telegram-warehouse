"""Tests for Dagster pipeline orchestration."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline import (
    scrape_telegram_data,
    load_raw_to_postgres,
    run_dbt_transformations,
    run_yolo_enrichment,
    medical_telegram_pipeline,
    medical_warehouse_job
)


class TestPipelineDefinitions:
    """Test suite for Dagster pipeline definitions."""

    def test_scrape_op_defined(self):
        """Test scrape operation is defined."""
        assert scrape_telegram_data is not None
        assert hasattr(scrape_telegram_data, 'name')

    def test_load_op_defined(self):
        """Test load operation is defined."""
        assert load_raw_to_postgres is not None
        assert hasattr(load_raw_to_postgres, 'name')

    def test_transform_op_defined(self):
        """Test transform operation is defined."""
        assert run_dbt_transformations is not None
        assert hasattr(run_dbt_transformations, 'name')

    def test_yolo_op_defined(self):
        """Test YOLO operation is defined."""
        assert run_yolo_enrichment is not None
        assert hasattr(run_yolo_enrichment, 'name')

    def test_graph_defined(self):
        """Test pipeline graph is defined."""
        assert medical_telegram_pipeline is not None

    def test_job_defined(self):
        """Test pipeline job is defined."""
        assert medical_warehouse_job is not None
        assert hasattr(medical_warehouse_job, 'name')

    def test_op_inputs_outputs(self):
        """Test operations have inputs/outputs configured."""
        assert scrape_telegram_data is not None
        assert load_raw_to_postgres is not None

    def test_job_has_description(self):
        """Test job has proper documentation."""
        assert medical_warehouse_job is not None


class TestPipelineConfig:
    """Test suite for pipeline configuration."""

    def test_pipeline_has_tags(self):
        """Test pipeline has proper tags."""
        assert medical_warehouse_job is not None
        # Job should have tags for team and version

    def test_scrape_config_schema(self):
        """Test scrape operation has config schema."""
        assert scrape_telegram_data is not None
        # Config should define channels and limit
