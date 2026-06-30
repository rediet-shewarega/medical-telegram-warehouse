from typing import List, Optional
from pydantic import BaseModel


class TopProduct(BaseModel):
    product_term: str
    mention_count: int


class ChannelActivityItem(BaseModel):
    post_date: str
    post_count: int
    avg_views: float
    total_forwards: int


class ChannelActivityResponse(BaseModel):
    channel_name: str
    activity: List[ChannelActivityItem]


class MessageSearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_date: str
    message_text: str
    view_count: int
    forward_count: int
    has_image: bool


class VisualContentItem(BaseModel):
    channel_name: str
    total_posts: int
    visual_posts: int
    visual_content_percentage: float


class ImageCategoryStats(BaseModel):
    image_category: str
    image_posts: int
    avg_views: float


class VisualContentResponse(BaseModel):
    by_channel: List[VisualContentItem]
    by_image_category: List[ImageCategoryStats]


class HealthResponse(BaseModel):
    status: str
    message: str