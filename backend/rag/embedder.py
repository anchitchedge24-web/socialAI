import logging
from typing import List
from sentence_transformers import SentenceTransformer
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if EmbeddingService._model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            EmbeddingService._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = EmbeddingService._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=32,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        embedding = EmbeddingService._model.encode(
            query,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding.tolist()