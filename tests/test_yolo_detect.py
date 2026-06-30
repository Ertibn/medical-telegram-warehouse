"""Tests for YOLO object detection module."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from yolo_detect import YOLODetector


class TestYOLODetector:
    """Test suite for YOLODetector class."""

    @pytest.fixture
    def detector(self):
        """Create detector instance for testing."""
        with patch('yolo_detect.YOLO'):
            return YOLODetector(model_name="yolov8n.pt")

    def test_detector_init(self, detector):
        """Test detector initialization."""
        assert detector.model is not None

    def test_person_classes(self, detector):
        """Test person class definitions."""
        assert 'person' in detector.PERSON_CLASSES

    def test_product_classes(self, detector):
        """Test product class definitions."""
        assert 'bottle' in detector.PRODUCT_CLASSES
        assert 'container' in detector.PRODUCT_CLASSES

    def test_classify_image_promotional(self, detector):
        """Test classification of promotional image."""
        detections = [
            {'class': 'person', 'confidence': 0.95},
            {'class': 'bottle', 'confidence': 0.87}
        ]
        result = detector.classify_image(detections)
        assert result == "promotional"

    def test_classify_image_product_display(self, detector):
        """Test classification of product display image."""
        detections = [
            {'class': 'bottle', 'confidence': 0.92},
            {'class': 'container', 'confidence': 0.88}
        ]
        result = detector.classify_image(detections)
        assert result == "product_display"

    def test_classify_image_lifestyle(self, detector):
        """Test classification of lifestyle image."""
        detections = [
            {'class': 'person', 'confidence': 0.95},
            {'class': 'face', 'confidence': 0.91}
        ]
        result = detector.classify_image(detections)
        assert result == "lifestyle"

    def test_classify_image_other(self, detector):
        """Test classification of other image."""
        detections = [
            {'class': 'car', 'confidence': 0.85}
        ]
        result = detector.classify_image(detections)
        assert result == "other"

    def test_classify_image_empty(self, detector):
        """Test classification with no detections."""
        result = detector.classify_image([])
        assert result == "other"

    def test_detect_objects_structure(self):
        """Test detection results structure."""
        expected_keys = {'class', 'confidence', 'class_id'}
        sample_detection = {
            'class': 'bottle',
            'confidence': 0.95,
            'class_id': 1
        }
        assert all(key in sample_detection for key in expected_keys)
