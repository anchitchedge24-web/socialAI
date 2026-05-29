import logging
from fastapi import APIRouter, HTTPException
from models.chat_models import AnalyzeRequest, AnalyzeResponse
from services.metadata_service import MetadataService
from rag.chunker import TranscriptChunker
from rag.embedder import EmbeddingService
from vectorstore.chroma_store import ChromaStore
from memory.conversation_memory import ConversationMemory
from utils.url_utils import validate_youtube_url, validate_instagram_url

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze-videos", response_model=AnalyzeResponse)
async def analyze_videos(request: AnalyzeRequest):
    if not validate_youtube_url(request.youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    if not validate_instagram_url(request.instagram_url):
        raise HTTPException(status_code=400, detail="Invalid Instagram URL")

    try:
        metadata_service = MetadataService()
        video_a, video_b = await metadata_service.process_videos(
            request.youtube_url,
            request.instagram_url,
        )
        await metadata_service.close()

        chunker = TranscriptChunker()
        all_chunks = chunker.chunk_both_videos(video_a, video_b)

        if not all_chunks:
            logger.warning("No chunks created")

        chroma = ChromaStore()
        chroma.clear_collection()

        if all_chunks:
            embedder = EmbeddingService()
            texts = [chunk.text for chunk in all_chunks]
            embeddings = embedder.embed_texts(texts)
            chroma.add_chunks(all_chunks, embeddings)

        memory = ConversationMemory()
        memory.clear_session("default")
        memory.set_video_context(
            "default",
            video_a.model_dump(),
            video_b.model_dump(),
        )

        return AnalyzeResponse(
            video_a=video_a.model_dump(),
            video_b=video_b.model_dump(),
            chunks_created=len(all_chunks),
            status="success",
            message=f"Analyzed both videos. Created {len(all_chunks)} chunks.",
        )

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")