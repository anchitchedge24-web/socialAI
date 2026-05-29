from typing import TypedDict, List, Dict, Any, Optional


class GraphState(TypedDict):
    query: str
    session_id: str
    conversation_history: str
    video_context: Dict[str, Any]
    retrieved_chunks: List[Dict[str, Any]]
    metadata_context: str
    reasoning: str
    answer: str
    evidence: List[str]
    sources: List[Dict[str, Any]]
    confidence: float
    error: Optional[str]