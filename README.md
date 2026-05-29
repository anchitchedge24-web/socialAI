# SocialRAG

Compare a YouTube video and an Instagram Reel side by side, then ask an LLM questions about them. Built this as a take-home project to play around with RAG pipelines and local LLMs.

The interesting bits:
- Extracts transcripts + metadata from both platforms
- Chunks → embeds → stores in Chroma
- Streams answers token-by-token via SSE
- Runs entirely locally (Ollama), no API keys needed
- Keeps conversation context across turns

## Demo

Paste two URLs, wait ~20 seconds, then chat:

> "Why did the YouTube video get more engagement than the reel?"
> "Compare the hooks in the first 5 seconds."
> "Suggest 3 improvements for the reel."

The bot pulls relevant transcript chunks, cross-references the engagement metrics, and streams back a grounded answer with source citations.

## Stack

**Backend**
- FastAPI + Uvicorn
- ChromaDB (local persistent)
- `sentence-transformers` with `BAAI/bge-small-en-v1.5`
- Ollama (llama3.2:3b by default)
- `youtube-transcript-api` + Whisper fallback
- `yt-dlp` for Instagram

**Frontend**
- React 18 + Vite
- Tailwind + Framer Motion
- Zustand for state (Redux is overkill here)
- SSE for streaming

## Prerequisites

You need:
- Python 3.10+
- Node 18+
- [Ollama](https://ollama.com) installed
- `ffmpeg` (for Whisper)
- A browser logged into Instagram (more on this below)

## Setup

### 1. Clone

```bash
git clone https://github.com/yourusername/social-rag-chatbot.git
cd social-rag-chatbot
```

### 2. Backend

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### 3. Install ffmpeg

Whisper needs this to process Instagram audio.

```bash
# Windows
winget install Gyan.FFmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### 4. Ollama

```bash
ollama pull llama3.2:3b
```

That's ~2GB. If you're tight on RAM, use `llama3.2:1b` instead and update `OLLAMA_MODEL` in `.env`.

Make sure Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

On Windows it auto-starts in the system tray. On Mac/Linux: `ollama serve`.

### 5. Instagram cookies (the annoying part)

Instagram blocks anonymous scraping. You need to feed yt-dlp your browser cookies so it looks like a logged-in session.

**Two options:**

**A) Read from browser** (easier, but flaky on Windows)

Just log into instagram.com in Chrome/Firefox/whatever, then in `.env`:
```env
INSTAGRAM_COOKIES_BROWSER=chrome
```

⚠️ **On Windows, Chrome locks its cookie DB while running.** You have to fully close Chrome (kill all `chrome.exe` in Task Manager) before starting the backend. This is painful, so I usually just use Firefox or option B.

**B) Export cookies to a file** (reliable, recommended)

1. Install a cookie export extension:
   - Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. Go to instagram.com (logged in), click the extension, export the file

3. Save it as `backend/cookies.txt`

4. In `.env`:
   ```env
   INSTAGRAM_COOKIES_FILE=./cookies.txt
   # comment out INSTAGRAM_COOKIES_BROWSER
   ```

5. Make sure it's in `.gitignore` (it already is, but double-check)

**Pro tip:** Use a throwaway Instagram account. Don't risk your main one getting flagged.

To verify cookies work before launching the backend:
```bash
yt-dlp --cookies-from-browser chrome --dump-json --no-download "https://www.instagram.com/reels/CzQJQvKJX1Z/"
```

If you get JSON, you're good. If you get "Login required", revisit the cookies setup.

### 6. Frontend

```bash
cd ../frontend
npm install
```

Done.

## Running it

Three terminals:

```bash
# Terminal 1 - Ollama (skip if auto-running)
ollama serve

# Terminal 2 - Backend
cd backend
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1
python main.py

# Terminal 3 - Frontend
cd frontend
npm run dev
```

Open http://localhost:5173

## How it works

When you submit two URLs:

1. **YouTube service** hits the oEmbed API + scrapes the watch page for view/like/comment counts, then pulls captions via `youtube-transcript-api`
2. **Instagram service** tries HTML parsing first (most reliable), falls back to `yt-dlp` with cookies. If transcripts aren't available, it downloads the video and runs Whisper
3. Both transcripts get chunked (500 words with 50-word overlap), embedded with BGE, and stored in Chroma with metadata
4. When you chat, a small graph runs:
   - parse input + load history
   - fetch metadata context
   - vector search for relevant chunks
   - build prompt with metadata + evidence + history
   - stream LLM response via Ollama
   - score confidence based on retrieval relevance
   - update memory

There's no actual LangGraph runtime — I wrote the nodes as plain functions because the orchestration is simple enough that the abstraction wasn't worth the dependency weight.

## Project layout

```
backend/
  api/routes/         # FastAPI endpoints
  services/           # YouTube, Instagram, Whisper, metadata orchestrator
  rag/
    graph/            # Pipeline nodes + state
    chunker.py
    embedder.py
    retriever.py
  vectorstore/        # Chroma wrapper
  memory/             # Session memory
  models/             # Pydantic schemas
  config/             # Settings
  utils/              # URL validation, text cleaning
  main.py
  .env

frontend/
  src/
    components/
      Chat/           # ChatPanel, ChatInput, ChatMessage, SourceCitation, TypingIndicator
      VideoCard/      # Card, MetadataBadge, EngagementBar, SkeletonCard
      VideoInput/     # Form, URLInput
      UI/             # GlassCard, Toast
    hooks/            # useChat, useVideoAnalysis, useSSE
    services/api.js
    store/appStore.js
    App.jsx
```

## Environment variables

Full `.env` reference:

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# LLM
USE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.7

# Embeddings
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# Chroma
CHROMA_PERSIST_DIR=./chroma_data
CHROMA_COLLECTION_NAME=video_comparison_collection
ANONYMIZED_TELEMETRY=false

# Chunking
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# Whisper (tiny | base | small | medium | large)
WHISPER_MODEL=base

# Frontend
FRONTEND_URL=http://localhost:5173

# Instagram auth — pick ONE
INSTAGRAM_COOKIES_BROWSER=chrome
# INSTAGRAM_COOKIES_FILE=./cookies.txt
```

## API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET    | `/api/health` | Health check + chunk count |
| POST   | `/api/analyze-videos` | Process both videos, build index |
| POST   | `/api/chat` | Stream chat response (SSE) |
| GET    | `/api/conversation-history?session_id=...` | Get session history |

`POST /api/chat` returns SSE events:
```
data: {"token": "Based"}
data: {"token": " on"}
data: {"done": true}
```

Swagger docs at http://localhost:8000/docs.

## Things to know

### View count estimation

Instagram doesn't reliably expose view counts via scraping. When the real number is missing, the app estimates from likes using an 8% like-to-view ratio (industry average for reels). It's usually within 15-20% of the real number — close enough for comparison purposes but not exact.

If you need real view counts, you'd need the Instagram Graph API (requires business account approval) or a paid service like RapidAPI.

### Engagement rate cap

I cap engagement rate at 100% because if it ever goes higher, the view data is wrong. Saw a few cases where Instagram returned 0 views but 4M likes, which produced absurd numbers.

### Memory

Session memory is just an in-memory dict keyed by `session_id`. Fine for one server. If you scale to multiple workers, swap it for Redis (it's trivial — the `ConversationMemory` class is the only thing that needs to change).

### Whisper is slow on CPU

First Instagram analysis takes ~30s if the video needs transcription. After that the model stays loaded so subsequent ones are faster. If you have a GPU, Whisper picks it up automatically.

### Chunking strategy

Word-based chunking with overlap. Could be smarter (sentence-aware, semantic boundaries) but for 1-3 minute videos this works fine. The retrieval quality is more limited by transcript quality than chunking strategy.

## Troubleshooting

**Backend won't start: `ModuleNotFoundError`**
You forgot to activate the venv. We've all done it.

**Pip install fails with langchain conflicts**
Use the requirements.txt as-is, don't pin different versions. If it still breaks, nuke `venv/` and rebuild.

**Ollama: `connection refused`**
Run `ollama serve` or check the system tray icon (Windows).

**Ollama: `model not found`**
You forgot to `ollama pull llama3.2:3b`. Or the model name in `.env` doesn't match what you pulled (check `ollama list`).

**Instagram: `Login required`**
Cookies aren't set up. Re-read step 5. On Windows, make sure Chrome is fully closed.

**Instagram: `Rate limited`**
You hit IG too many times. Wait 10 minutes.

**YouTube: `no element found`**
The video doesn't have captions. Try a different video.

**Views showing as 50K placeholder**
yt-dlp couldn't get real views and the estimation fallback didn't trigger because there were no likes either. Try a more popular video.

**Whisper: `ffmpeg not found`**
Install ffmpeg (step 3).

**Chroma telemetry spam in logs**
Add `ANONYMIZED_TELEMETRY=false` to `.env`.

## Performance notes

On my machine (M1 Mac, 16GB):
- Cold start analysis: ~20-30s (includes downloading Whisper model first time)
- Subsequent analyses: ~10-15s
- First chat token: ~500ms-1s
- Streaming speed: ~80 tokens/sec

On a Windows laptop without GPU it's noticeably slower, maybe 25-30 tokens/sec from Ollama. Still feels live thanks to streaming.

## If you wanted to scale this

For a single user it's fine as-is. If you wanted to run it as a service:

| What | Swap to |
|------|---------|
| ChromaDB local | Qdrant or Pinecone |
| Ollama local | vLLM or TGI on a GPU box |
| In-memory sessions | Redis with TTL |
| Synchronous processing | Celery workers + Redis broker |
| Single uvicorn | Multiple workers behind a load balancer |
| Local file storage | S3 |

Embedding cache would also be a quick win — content-hash the transcript, skip re-embedding if seen before. Useful when the same video gets analyzed multiple times.

Cost-wise, the whole thing runs at $0 on local hardware. A GPU server on RunPod or similar runs ~$100-200/month if you want it always-on.

## Things I'd add if I had more time

- TikTok support (yt-dlp handles it, just need a service wrapper)
- Better chunking (semantic boundaries via spaCy)
- Embedding cache (content-hash keyed)
- Proper error boundaries in the React app
- Tests (yeah, I know)
- Export chat as PDF/markdown
- Auth + multi-session

## Notes on the architecture choices

A few things people might ask about:

**Why not LangChain/LangGraph for real?**
I import them in requirements but the actual pipeline is just plain Python functions calling each other. The orchestration here is straightforward — input → retrieve → reason → format → stream. Adding LangGraph's runtime would mean another layer of state management and abstraction for no real benefit. If the pipeline gets branchier (conditional retrieval, parallel agents, etc.), the abstraction would start paying for itself.

**Why BGE-small over OpenAI embeddings?**
Free, fast, ~3% worse on benchmarks. For comparing 24-50 chunks per session, you'll never notice the quality difference.

**Why Ollama over hosted APIs?**
Zero per-token cost, no rate limits, no API keys to manage, works offline. The downside is slower inference on CPU, but streaming hides most of that. For a project where the user explicitly wants "low cost," local LLM is the right call.

**Why SSE over WebSockets?**
SSE is one-way (server → client), which is all we need. Simpler protocol, auto-reconnects, works over plain HTTP. WebSockets are great when you need bidirectional, but here it'd just be ceremony.

**Why Zustand?**
60KB of Redux + boilerplate for a 3-store-key app is silly. Zustand is 1KB and the API is `set()` / `get()`. Done.

## License

MIT. Do whatever.#   s o c i a l A I  
 