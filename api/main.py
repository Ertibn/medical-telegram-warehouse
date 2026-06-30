"""
Task 4: Analytical API
FastAPI endpoints for querying medical telegram data warehouse.
"""

import logging
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    TopProductsResponse, ProductMetric,
    ChannelActivity, MessageSearchResponse, Message,
    VisualContentStats, ImageCategoryStats
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Medical Telegram Data Warehouse API",
    description="Analytical API for Ethiopian medical business Telegram data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "medical-telegram-warehouse-api"}


@app.get(
    "/api/reports/top-products",
    response_model=TopProductsResponse,
    tags=["Reports"],
    summary="Get top products",
    description="Returns the most frequently mentioned products across all channels"
)
async def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of top products to return"),
    db: Session = Depends(get_db)
):
    """
    Get most frequently mentioned products across channels.
    
    - **limit**: Number of results (default: 10, max: 100)
    """
    try:
        query = """
            SELECT 
                LOWER(message_text) as text,
                COUNT(*) as frequency,
                ROUND(AVG(views), 2) as avg_views,
                ROUND(AVG(forwards), 0)::integer as avg_forwards
            FROM marts.fct_messages
            WHERE message_text IS NOT NULL AND TRIM(message_text) != ''
            GROUP BY LOWER(message_text)
            ORDER BY frequency DESC
            LIMIT :limit
        """
        
        result = db.execute(text(query), {"limit": limit})
        products = []
        
        for row in result:
            # Extract product terms from message (first 50 chars)
            product_text = row[0][:50] if row[0] else "Unknown"
            
            products.append(ProductMetric(
                product=product_text,
                frequency=int(row[1]),
                avg_views=float(row[2]) if row[2] else 0,
                avg_forwards=int(row[3]) if row[3] else 0
            ))
        
        return TopProductsResponse(
            total_unique_products=len(products),
            top_products=products
        )
    
    except Exception as e:
        logger.error(f"Error in get_top_products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get(
    "/api/channels/{channel_name}/activity",
    response_model=ChannelActivity,
    tags=["Channels"],
    summary="Get channel activity",
    description="Returns posting activity and engagement metrics for a specific channel"
)
async def get_channel_activity(
    channel_name: str = Query(..., description="Name of the channel"),
    db: Session = Depends(get_db)
):
    """
    Get activity metrics for a specific channel.
    
    - **channel_name**: Name of the Telegram channel
    """
    try:
        query = """
            SELECT 
                dc.channel_name,
                COUNT(fm.message_id) as total_messages,
                SUM(fm.views)::integer as total_views,
                ROUND(AVG(fm.views), 2) as avg_views,
                SUM(fm.forwards)::integer as total_forwards,
                ROUND(AVG(fm.forwards), 2) as avg_forwards,
                COUNT(CASE WHEN fm.has_media THEN 1 END) as messages_with_images,
                ROUND(
                    COUNT(CASE WHEN fm.has_media THEN 1 END)::numeric / 
                    COUNT(fm.message_id) * 100, 2
                ) as image_percentage,
                MIN(dd.full_date)::text as min_date,
                MAX(dd.full_date)::text as max_date
            FROM marts.fct_messages fm
            JOIN marts.dim_channels dc ON fm.channel_key = dc.channel_key
            JOIN marts.dim_dates dd ON fm.date_key = dd.date_key
            WHERE LOWER(dc.channel_name) = LOWER(:channel_name)
            GROUP BY dc.channel_name
        """
        
        result = db.execute(text(query), {"channel_name": channel_name}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")
        
        return ChannelActivity(
            channel_name=result[0],
            total_messages=result[1],
            total_views=result[2],
            avg_views_per_message=float(result[3]) if result[3] else 0,
            total_forwards=result[4],
            avg_forwards_per_message=float(result[5]) if result[5] else 0,
            messages_with_images=result[6],
            image_percentage=float(result[7]) if result[7] else 0,
            date_range=f"{result[8]} to {result[9]}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_channel_activity: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get(
    "/api/search/messages",
    response_model=MessageSearchResponse,
    tags=["Search"],
    summary="Search messages",
    description="Search for messages containing a specific keyword"
)
async def search_messages(
    query: str = Query(..., min_length=1, max_length=100, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Search messages by keyword.
    
    - **query**: Search term (e.g., 'paracetamol')
    - **limit**: Number of results (default: 20, max: 100)
    """
    try:
        search_term = f"%{query}%"
        
        sql_query = """
            SELECT 
                fm.message_id,
                dc.channel_name,
                dd.full_date::text,
                fm.message_text,
                fm.views,
                fm.forwards,
                fm.has_media
            FROM marts.fct_messages fm
            JOIN marts.dim_channels dc ON fm.channel_key = dc.channel_key
            JOIN marts.dim_dates dd ON fm.date_key = dd.date_key
            WHERE LOWER(fm.message_text) LIKE LOWER(:search_term)
            ORDER BY fm.views DESC
            LIMIT :limit
        """
        
        result = db.execute(
            text(sql_query),
            {"search_term": search_term, "limit": limit}
        )
        
        messages = []
        for row in result:
            messages.append(Message(
                message_id=row[0],
                channel_name=row[1],
                message_date=row[2],
                message_text=row[3][:100] + "..." if len(row[3]) > 100 else row[3],
                views=row[4],
                forwards=row[5],
                has_image=bool(row[6])
            ))
        
        return MessageSearchResponse(
            query=query,
            total_results=len(messages),
            messages=messages
        )
    
    except Exception as e:
        logger.error(f"Error in search_messages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get(
    "/api/reports/visual-content",
    response_model=VisualContentStats,
    tags=["Reports"],
    summary="Get visual content statistics",
    description="Returns statistics about image usage and YOLO detections"
)
async def get_visual_content_stats(
    db: Session = Depends(get_db)
):
    """
    Get visual content statistics across channels.
    Includes image categories and channel breakdowns.
    """
    try:
        # Get overall stats
        overall_query = """
            SELECT 
                COUNT(DISTINCT fm.message_id) as total_with_images,
                COUNT(DISTINCT fm.message_id) as total_images,
                ROUND(
                    COUNT(DISTINCT fm.message_id)::numeric / 
                    (SELECT COUNT(DISTINCT message_id) FROM marts.fct_messages) * 100, 2
                ) as overall_percentage
            FROM marts.fct_messages fm
            WHERE fm.has_media = true
        """
        
        overall_result = db.execute(text(overall_query)).fetchone()
        
        # Get stats by category (if image detection table exists)
        category_query = """
            SELECT 
                COALESCE(fid.image_category, 'unknown') as category,
                COUNT(*) as count,
                ROUND(COUNT(*)::numeric / 
                    (SELECT COUNT(*) FROM marts.fct_image_detections) * 100, 2) as percentage,
                ROUND(AVG(fm.views), 2) as avg_views,
                ROUND(AVG(fm.forwards), 2) as avg_forwards
            FROM marts.fct_image_detections fid
            JOIN marts.fct_messages fm ON fid.message_id = fm.message_id
            GROUP BY fid.image_category
            ORDER BY count DESC
        """
        
        category_results = []
        try:
            for row in db.execute(text(category_query)):
                category_results.append(ImageCategoryStats(
                    category=row[0],
                    count=int(row[1]),
                    percentage=float(row[2]),
                    avg_views=float(row[3]) if row[3] else 0,
                    avg_forwards=float(row[4]) if row[4] else 0
                ))
        except:
            logger.warning("Image detection table not available")
        
        # Get stats by channel
        channel_query = """
            SELECT 
                dc.channel_name,
                COUNT(CASE WHEN fm.has_media THEN 1 END) as count,
                ROUND(
                    COUNT(CASE WHEN fm.has_media THEN 1 END)::numeric / 
                    COUNT(*) * 100, 2
                ) as percentage
            FROM marts.fct_messages fm
            JOIN marts.dim_channels dc ON fm.channel_key = dc.channel_key
            GROUP BY dc.channel_name
            ORDER BY count DESC
        """
        
        channel_stats = {}
        for row in db.execute(text(channel_query)):
            channel_stats[row[0]] = {
                "count": int(row[1]),
                "percentage": float(row[2])
            }
        
        return VisualContentStats(
            total_messages_with_images=int(overall_result[0]) if overall_result[0] else 0,
            total_images=int(overall_result[1]) if overall_result[1] else 0,
            overall_percentage=float(overall_result[2]) if overall_result[2] else 0,
            by_category=category_results,
            by_channel=channel_stats
        )
    
    except Exception as e:
        logger.error(f"Error in get_visual_content_stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/", tags=["Root"], summary="API Root")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Medical Telegram Data Warehouse API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "top_products": "/api/reports/top-products",
            "channel_activity": "/api/channels/{channel_name}/activity",
            "search": "/api/search/messages",
            "visual_content": "/api/reports/visual-content"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
