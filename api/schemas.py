"""
Pydantic schemas for API request/response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ProductMetric(BaseModel):
    """Response model for product metrics."""
    product: str = Field(..., description="Product name or term")
    frequency: int = Field(..., description="Number of mentions")
    avg_views: float = Field(..., description="Average views for messages with this product")
    avg_forwards: int = Field(..., description="Average forwards")

    class Config:
        schema_extra = {
            "example": {
                "product": "Paracetamol 500mg",
                "frequency": 45,
                "avg_views": 850.5,
                "avg_forwards": 12
            }
        }


class TopProductsResponse(BaseModel):
    """Response for top products endpoint."""
    total_unique_products: int
    top_products: List[ProductMetric]

    class Config:
        schema_extra = {
            "example": {
                "total_unique_products": 156,
                "top_products": [
                    {
                        "product": "Paracetamol 500mg",
                        "frequency": 45,
                        "avg_views": 850.5,
                        "avg_forwards": 12
                    }
                ]
            }
        }


class ChannelActivity(BaseModel):
    """Response model for channel activity."""
    channel_name: str
    total_messages: int
    total_views: int
    avg_views_per_message: float
    total_forwards: int
    avg_forwards_per_message: float
    messages_with_images: int
    image_percentage: float
    date_range: str

    class Config:
        schema_extra = {
            "example": {
                "channel_name": "CheMed",
                "total_messages": 200,
                "total_views": 150000,
                "avg_views_per_message": 750.0,
                "total_forwards": 2500,
                "avg_forwards_per_message": 12.5,
                "messages_with_images": 120,
                "image_percentage": 60.0,
                "date_range": "2026-06-01 to 2026-06-28"
            }
        }


class Message(BaseModel):
    """Response model for individual message."""
    message_id: int
    channel_name: str
    message_date: str
    message_text: str
    views: int
    forwards: int
    has_image: bool

    class Config:
        schema_extra = {
            "example": {
                "message_id": 1,
                "channel_name": "CheMed",
                "message_date": "2026-06-28",
                "message_text": "Paracetamol 500mg available now",
                "views": 850,
                "forwards": 12,
                "has_image": True
            }
        }


class MessageSearchResponse(BaseModel):
    """Response for message search endpoint."""
    query: str
    total_results: int
    messages: List[Message]

    class Config:
        schema_extra = {
            "example": {
                "query": "paracetamol",
                "total_results": 45,
                "messages": []
            }
        }


class ImageCategoryStats(BaseModel):
    """Response model for image category statistics."""
    category: str
    count: int
    percentage: float
    avg_views: float
    avg_forwards: float

    class Config:
        schema_extra = {
            "example": {
                "category": "promotional",
                "count": 150,
                "percentage": 25.0,
                "avg_views": 900.5,
                "avg_forwards": 15.2
            }
        }


class VisualContentStats(BaseModel):
    """Response for visual content statistics."""
    total_messages_with_images: int
    total_images: int
    overall_percentage: float
    by_category: List[ImageCategoryStats]
    by_channel: dict

    class Config:
        schema_extra = {
            "example": {
                "total_messages_with_images": 600,
                "total_images": 600,
                "overall_percentage": 60.0,
                "by_category": [],
                "by_channel": {"CheMed": {"count": 120, "percentage": 20.0}}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    status_code: int

    class Config:
        schema_extra = {
            "example": {
                "detail": "Resource not found",
                "status_code": 404
            }
        }
