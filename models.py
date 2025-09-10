from typing import List
from pydantic import BaseModel, Field

class NewsItem(BaseModel):
    title: str = Field(description="News article title")
    summary: str = Field(description="Brief summary of the article")
    url: str = Field(description="Article URL")
    timestamp: str = Field(description="Publication timestamp")
    relevance_score: float = Field(description="Relevance score 0-1")

class MarketSummary(BaseModel):
    summary_text: str = Field(description="Market summary text")
    key_points: List[str] = Field(description="Key market points")
    charts_urls: List[str] = Field(description="URLs of relevant charts/images")
    language: str = Field(description="Language of the summary")

class FormattedReport(BaseModel):
    content: str = Field(description="Formatted report content with image placeholders")
    image_urls: List[str] = Field(description="List of image URLs to include")
    chart_descriptions: List[str] = Field(description="Descriptions of where to place charts")
