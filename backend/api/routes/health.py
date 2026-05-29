from fastapi import APIRouter
from vectorstore.chroma_store import ChromaStore

router = APIRouter()


@router.get("/health")
async def health_check():
    try:
        chroma = ChromaStore()
        count = chroma.get_count()
        return {
            "status": "healthy",
            "vector_store_chunks": count,
            "service": "Social Media RAG Chatbot",
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
        }