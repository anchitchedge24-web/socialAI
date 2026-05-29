from pydantic import BaseModel, Field
from typing import List, Optional


class SourceCitation(BaseModel):
    video_id: str
    chunk_id: str
    text_snippet: str
    relevance_score: float
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: str = Field(default="default", description="Session identifier")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    reasoning: str = Field(default="", description="Reasoning explanation")
    evidence: List[str] = Field(default_factory=list, description="Evidence snippets")
    sources: List[SourceCitation] = Field(default_factory=list, description="Source citations")
    confidence: float = Field(default=0.0, description="Confidence score 0-1")


class AnalyzeRequest(BaseModel):
    youtube_url: str = Field(..., description="YouTube video URL")
    instagram_url: str = Field(..., description="Instagram reel URL")


class AnalyzeResponse(BaseModel):
    video_a: dict = Field(..., description="Video A (YouTube) metadata")
    video_b: dict = Field(..., description="Video B (Instagram) metadata")
    chunks_created: int = Field(default=0)
    status: str = Field(default="success")
    message: str = Field(default="")