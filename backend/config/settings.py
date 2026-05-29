from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # LLM Provider Selection
    USE_OLLAMA: bool = True
    USE_GROQ: bool = False

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # LLM common
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.7
    LLM_CONTEXT_LENGTH: int = 4096
    LLM_MODEL_PATH: str = "./models/llama-2-7b-chat.Q4_K_M.gguf"

    # 🔥 NEW: YouTube Data API
    YOUTUBE_API_KEY: str = ""

    # Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # Chroma
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_NAME: str = "video_comparison_collection"

    # Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # Whisper
    WHISPER_MODEL: str = "base"

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    return Settings()