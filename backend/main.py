import sys
import os

# Ensure the backend directory is in sys.path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging

load_dotenv()

from config.settings import get_settings
from api.routes.analyze import router as analyze_router
from api.routes.chat import router as chat_router
from api.routes.health import router as health_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Social Media RAG Chatbot Backend...")

    # 🔥 Decode Instagram cookies from env var (for cloud deployment)
    cookies_b64 = os.getenv("INSTAGRAM_COOKIES_BASE64")
    if cookies_b64:
        import base64
        try:
            cookies_content = base64.b64decode(cookies_b64).decode("utf-8")
            cookies_path = "/app/cookies.txt"
            with open(cookies_path, "w") as f:
                f.write(cookies_content)
            os.environ["INSTAGRAM_COOKIES_FILE"] = cookies_path
            # CRITICAL: unset browser-based cookies so file-based is used
            os.environ.pop("INSTAGRAM_COOKIES_BROWSER", None)
            logger.info(f"✅ Instagram cookies loaded from env variable ({len(cookies_content)} bytes)")
        except Exception as e:
            logger.error(f"❌ Failed to decode Instagram cookies: {e}")
    else:
        logger.warning("⚠️ INSTAGRAM_COOKIES_BASE64 not set — Instagram extraction will fail in production")

    logger.info(f"ChromaDB persist dir: {settings.CHROMA_PERSIST_DIR}")
    logger.info(f"Embedding model: {settings.EMBEDDING_MODEL}")
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    os.makedirs("./temp_downloads", exist_ok=True)
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="Social Media RAG Chatbot",
    description="RAG-powered chatbot for comparing social media videos",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
allowed_origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
]

prod_frontend = os.getenv("PROD_FRONTEND_URL")
if prod_frontend:
    allowed_origins.append(prod_frontend)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])

# This block runs ONLY for local development (python main.py)
# Production uses uvicorn CLI directly via Dockerfile CMD
if __name__ == "__main__":
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )