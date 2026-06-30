"""
Task 3: YOLO Object Detection for Image Enrichment
Scans downloaded images and performs object detection using YOLOv8.
Classifies images and saves results to CSV for warehouse integration.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
from ultralytics import YOLO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/yolo_detect.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class YOLODetector:
    """Performs object detection on images using YOLOv8."""

    # Object classes relevant to medical/cosmetic domain
    PERSON_CLASSES = {'person'}
    PRODUCT_CLASSES = {
        'bottle', 'container', 'jar', 'box', 'package',
        'cup', 'bowl', 'product'
    }
    LIFESTYLE_CLASSES = {'person', 'face', 'hand'}

    def __init__(self, model_name: str = "yolov8n.pt"):
        """
        Initialize YOLO detector with nano model.
        
        Args:
            model_name: YOLO model to use (nano for efficiency)
        """
        self.model = YOLO(model_name)
        logger.info(f"Loaded YOLO model: {model_name}")

    def detect_objects(self, image_path: str) -> List[Dict]:
        """
        Run object detection on an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detected objects with confidence scores
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                logger.warning(f"Failed to read image: {image_path}")
                return []

            # Run detection
            results = self.model(img)
            
            detections = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    detections.append({
                        'class': class_name,
                        'confidence': confidence,
                        'class_id': class_id
                    })
            
            return detections

        except Exception as e:
            logger.error(f"Error detecting objects in {image_path}: {e}")
            return []

    def classify_image(self, detections: List[Dict]) -> str:
        """
        Classify image based on detected objects.
        
        Args:
            detections: List of detected objects
            
        Returns:
            Image category: promotional, product_display, lifestyle, or other
        """
        if not detections:
            return "other"
        
        detected_classes = {det['class'].lower() for det in detections}
        has_person = any(cls in detected_classes for cls in self.PERSON_CLASSES)
        has_product = any(cls in detected_classes for cls in self.PRODUCT_CLASSES)
        
        # Classification logic
        if has_person and has_product:
            return "promotional"
        elif has_product and not has_person:
            return "product_display"
        elif has_person and not has_product:
            return "lifestyle"
        else:
            return "other"

    def process_images_dir(
        self,
        images_dir: str = "data/raw/images",
        output_csv: str = "data/yolo_results.csv"
    ) -> int:
        """
        Process all images in directory and save results to CSV.
        
        Args:
            images_dir: Directory containing channel subdirectories
            output_csv: Output CSV file path
            
        Returns:
            Number of images processed
        """
        images_path = Path(images_dir)
        results = []
        processed_count = 0
        
        if not images_path.exists():
            logger.error(f"Images directory not found: {images_dir}")
            return 0
        
        # Iterate through channel directories
        for channel_dir in images_path.iterdir():
            if not channel_dir.is_dir():
                continue
            
            logger.info(f"Processing channel: {channel_dir.name}")
            
            # Process each image
            for img_file in channel_dir.glob("*.jpg"):
                try:
                    # Extract message_id from filename
                    message_id = int(img_file.stem)
                    
                    # Run detection
                    detections = self.detect_objects(str(img_file))
                    
                    if detections:
                        # Get most confident detection
                        top_detection = max(detections, key=lambda x: x['confidence'])
                        
                        # Classify image
                        image_category = self.classify_image(detections)
                        
                        results.append({
                            'message_id': message_id,
                            'channel_name': channel_dir.name,
                            'detected_class': top_detection['class'],
                            'confidence_score': round(top_detection['confidence'], 3),
                            'image_category': image_category,
                            'num_objects': len(detections)
                        })
                        
                        processed_count += 1
                        
                        if processed_count % 10 == 0:
                            logger.info(f"Processed {processed_count} images")
                    
                except Exception as e:
                    logger.warning(f"Error processing image {img_file}: {e}")
                    continue
        
        # Save results to CSV
        if results:
            self._save_results(results, output_csv)
        
        logger.info(f"Total images processed: {processed_count}")
        return processed_count

    def _save_results(self, results: List[Dict], output_csv: str):
        """Save detection results to CSV."""
        try:
            Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        'message_id', 'channel_name', 'detected_class',
                        'confidence_score', 'image_category', 'num_objects'
                    ]
                )
                writer.writeheader()
                writer.writerows(results)
            
            logger.info(f"Saved {len(results)} results to {output_csv}")
        except Exception as e:
            logger.error(f"Error saving results to CSV: {e}")

    def get_statistics(self, output_csv: str = "data/yolo_results.csv") -> Dict:
        """
        Generate statistics from detection results.
        
        Args:
            output_csv: Path to results CSV
            
        Returns:
            Dictionary of statistics
        """
        try:
            import pandas as pd
            
            if not Path(output_csv).exists():
                logger.warning(f"Results file not found: {output_csv}")
                return {}
            
            df = pd.read_csv(output_csv)
            
            stats = {
                'total_images': len(df),
                'images_by_category': df['image_category'].value_counts().to_dict(),
                'images_by_channel': df['channel_name'].value_counts().to_dict(),
                'avg_confidence': round(df['confidence_score'].mean(), 3),
                'top_detected_class': df['detected_class'].value_counts().head(5).to_dict()
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error generating statistics: {e}")
            return {}


def main():
    """Main entry point."""
    logger.info("Starting YOLO object detection")
    
    # Initialize detector
    detector = YOLODetector(model_name="yolov8n.pt")
    
    # Process images
    processed = detector.process_images_dir(
        images_dir="data/raw/images",
        output_csv="data/yolo_results.csv"
    )
    
    # Generate statistics
    stats = detector.get_statistics("data/yolo_results.csv")
    
    logger.info("=" * 60)
    logger.info("YOLO DETECTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total images processed: {stats.get('total_images', 0)}")
    logger.info(f"Images by category: {stats.get('images_by_category', {})}")
    logger.info(f"Images by channel: {stats.get('images_by_channel', {})}")
    logger.info(f"Average confidence: {stats.get('avg_confidence', 0)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
