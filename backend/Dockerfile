FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pin pip + setuptools FIRST to avoid pkg_resources issue
RUN pip install --no-cache-dir --upgrade "pip==24.0" "setuptools==69.0.3" "wheel==0.42.0"

# Copy requirements first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p chroma_data temp_downloads

# Set PYTHONPATH so all nested imports work
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

EXPOSE 10000

# 🔥 CRITICAL: Use uvicorn CLI directly (NOT python main.py)
# This ensures Python's module system treats /app as the package root
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]