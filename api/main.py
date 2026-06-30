from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import (
    ChannelActivityResponse,
    HealthResponse,
    MessageSearchResult,
    TopProduct,
    VisualContentResponse,
)


app = FastAPI(
    title="Medical Telegram Analytical API",
    description="REST API for analyzing Ethiopian medical Telegram warehouse data.",
    version="1.0.0",
)


@app.get("/", response_model=HealthResponse, tags=["Health"])
def root():
    return {
        "status": "ok",
        "message": "Medical Telegram Analytical API is running.",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "message": "Database-backed API service is healthy.",
    }


@app.get(
    "/api/reports/top-products",
    response_model=List[TopProduct],
    tags=["Reports"],
    summary="Get top mentioned product terms",
)
def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of top product terms to return."),
    db: Session = Depends(get_db),
):
    query = text(
        """
        WITH words AS (
            SELECT
                REGEXP_REPLACE(word, '[^[:alnum:]]', '', 'g') AS product_term
            FROM public_marts.fct_messages,
                 REGEXP_SPLIT_TO_TABLE(LOWER(COALESCE(message_text, '')), '\\s+') AS word
        ),
        filtered_words AS (
            SELECT product_term
            FROM words
            WHERE LENGTH(product_term) >= 4
              AND product_term NOT IN (
                  'this', 'that', 'with', 'from', 'have', 'your', 'will',
                  'available', 'currently', 'contact', 'phone', 'price',
                  'more', 'only', 'please', 'telegram', 'medical'
              )
              AND product_term !~ '^[0-9]+$'
        )
        SELECT
            product_term,
            COUNT(*)::INT AS mention_count
        FROM filtered_words
        GROUP BY product_term
        ORDER BY mention_count DESC
        LIMIT :limit
        """
    )

    rows = db.execute(query, {"limit": limit}).mappings().all()
    return rows


@app.get(
    "/api/channels/{channel_name}/activity",
    response_model=ChannelActivityResponse,
    tags=["Channels"],
    summary="Get posting activity for a channel",
)
def get_channel_activity(
    channel_name: str,
    db: Session = Depends(get_db),
):
    query = text(
        """
        SELECT
            c.channel_name,
            d.full_date::TEXT AS post_date,
            COUNT(*)::INT AS post_count,
            ROUND(AVG(f.view_count)::NUMERIC, 2)::FLOAT AS avg_views,
            COALESCE(SUM(f.forward_count), 0)::INT AS total_forwards
        FROM public_marts.fct_messages f
        JOIN public_marts.dim_channels c
            ON f.channel_key = c.channel_key
        JOIN public_marts.dim_dates d
            ON f.date_key = d.date_key
        WHERE LOWER(c.channel_name) = LOWER(:channel_name)
        GROUP BY c.channel_name, d.full_date
        ORDER BY d.full_date
        """
    )

    rows = db.execute(query, {"channel_name": channel_name}).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No activity found for channel '{channel_name}'.",
        )

    return {
        "channel_name": rows[0]["channel_name"],
        "activity": rows,
    }


@app.get(
    "/api/search/messages",
    response_model=List[MessageSearchResult],
    tags=["Search"],
    summary="Search Telegram messages by keyword",
)
def search_messages(
    query: str = Query(..., min_length=2, description="Keyword to search for, for example paracetamol."),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of messages to return."),
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT
            f.message_id::INT AS message_id,
            c.channel_name,
            d.full_date::TEXT AS message_date,
            f.message_text,
            f.view_count::INT AS view_count,
            f.forward_count::INT AS forward_count,
            f.has_image::BOOLEAN AS has_image
        FROM public_marts.fct_messages f
        JOIN public_marts.dim_channels c
            ON f.channel_key = c.channel_key
        JOIN public_marts.dim_dates d
            ON f.date_key = d.date_key
        WHERE f.message_text ILIKE :search_query
        ORDER BY f.view_count DESC
        LIMIT :limit
        """
    )

    rows = db.execute(
        sql,
        {
            "search_query": f"%{query}%",
            "limit": limit,
        },
    ).mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No messages found containing '{query}'.",
        )

    return rows


@app.get(
    "/api/reports/visual-content",
    response_model=VisualContentResponse,
    tags=["Reports"],
    summary="Get visual content statistics",
)
def get_visual_content_stats(db: Session = Depends(get_db)):
    by_channel_query = text(
        """
        WITH image_posts AS (
            SELECT DISTINCT
                message_id,
                channel_key
            FROM public_marts.fct_image_detections
        )
        SELECT
            c.channel_name,
            COUNT(DISTINCT f.message_id)::INT AS total_posts,
            COUNT(DISTINCT i.message_id)::INT AS visual_posts,
            ROUND(
                100.0 * COUNT(DISTINCT i.message_id)
                / NULLIF(COUNT(DISTINCT f.message_id), 0),
                2
            )::FLOAT AS visual_content_percentage
        FROM public_marts.fct_messages f
        JOIN public_marts.dim_channels c
            ON f.channel_key = c.channel_key
        LEFT JOIN image_posts i
            ON f.message_id = i.message_id
           AND f.channel_key = i.channel_key
        GROUP BY c.channel_name
        ORDER BY visual_content_percentage DESC
        """
    )

    by_category_query = text(
        """
        WITH image_posts AS (
            SELECT DISTINCT
                message_id,
                channel_key,
                image_category
            FROM public_marts.fct_image_detections
        )
        SELECT
            i.image_category,
            COUNT(*)::INT AS image_posts,
            ROUND(AVG(f.view_count)::NUMERIC, 2)::FLOAT AS avg_views
        FROM image_posts i
        JOIN public_marts.fct_messages f
            ON i.message_id = f.message_id
           AND i.channel_key = f.channel_key
        GROUP BY i.image_category
        ORDER BY avg_views DESC
        """
    )

    by_channel = db.execute(by_channel_query).mappings().all()
    by_image_category = db.execute(by_category_query).mappings().all()

    return {
        "by_channel": by_channel,
        "by_image_category": by_image_category,
    }