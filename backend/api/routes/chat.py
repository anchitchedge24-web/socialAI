import logging
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models.chat_models import ChatRequest
from rag.graph.pipeline import RAGPipeline
from memory.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)

router = APIRouter()
pipeline = RAGPipeline()
memory = ConversationMemory()


@router.post("/chat")
async def chat_stream(request: ChatRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    async def event_generator():
        try:
            async for token in pipeline.stream_response(
                query=request.message,
                session_id=request.session_id,
            ):
                data = json.dumps({"token": token})
                yield f"data: {data}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            error_data = json.dumps({"error": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversation-history")
async def get_history(session_id: str = "default"):
    history = memory.get_history(session_id)
    return {"session_id": session_id, "messages": history}