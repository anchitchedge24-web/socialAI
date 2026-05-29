FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pin pip + setuptools FIRST
RUN pip install --no-cache-dir --upgrade "pip==24.0" "setuptools==69.0.3" "wheel==0.42.0"

# Copy requirements first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p chroma_data temp_downloads

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

EXPOSE 10000

# 🔍 DEBUG: Print directory structure + Python path BEFORE starting
# This will show us exactly what's going wrong
CMD ["sh", "-c", "\
    echo '===== DIRECTORY STRUCTURE =====' && \
    ls -la /app && \
    echo '===== MODELS FOLDER =====' && \
    ls -la /app/models/ && \
    echo '===== PYTHON PATH =====' && \
    python -c 'import sys; print(sys.path)' && \
    echo '===== TRYING IMPORT =====' && \
    python -c 'from models.chat_models import ChatRequest; print(\"✅ Import works!\")' && \
    echo '===== STARTING UVICORN =====' && \
    uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} \
"]