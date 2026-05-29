from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VideoMetadata(BaseModel):
    video_id: str = Field(..., description="Identifier: 'A' or 'B'")
    platform: str = Field(..., description="youtube or instagram")
    url: str = Field(..., description="Original URL")
    title: str = Field(default="Unknown")
    description: str = Field(default="")
    creator_name: str = Field(default="Unknown")
    follower_count: Optional[int] = Field(default=None)
    views: int = Field(default=0)
    likes: int = Field(default=0)
    comments: int = Field(default=0)
    engagement_rate: float = Field(default=0.0)
    upload_date: Optional[str] = Field(default=None)
    duration: Optional[float] = Field(default=None)
    duration_formatted: Optional[str] = Field(default=None)
    thumbnail: Optional[str] = Field(default=None)
    hashtags: List[str] = Field(default_factory=list)
    transcript: str = Field(default="")
    transcript_available: bool = Field(default=False)

    def compute_engagement_rate(self):
        if self.views > 0:
            rate = ((self.likes + self.comments) / self.views) * 100
            # Cap at 100% — anything higher means views data is unreliable
            self.engagement_rate = round(min(rate, 100.0), 2)
        else:
            self.engagement_rate = 0.0

    def format_duration(self):
        if self.duration:
            mins = int(self.duration // 60)
            secs = int(self.duration % 60)
            self.duration_formatted = f"{mins}:{secs:02d}"