from pydantic import BaseModel, Field
from typing import Optional


class TextChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    video_id: str = Field(..., description="'A' or 'B'")
    text: str = Field(..., description="Chunk text content")
    creator_name: str = Field(default="Unknown")
    source_platform: str = Field(default="unknown")
    timestamp_start: Optional[float] = Field(default=None)
    timestamp_end: Optional[float] = Field(default=None)
    chunk_index: int = Field(default=0)
    total_chunks: int = Field(default=0)