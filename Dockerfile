# Use Python 3.10 for Render
FROM python:3.10-slim

WORKDIR /app

# Minimal system deps (curl for healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Runtime env
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000  

# Install Python deps first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data/day_nutrition

# Expose nominal port (informational)
EXPOSE 8000

# Health check against whatever PORT Render assigns
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD sh -c 'curl -fsS http://127.0.0.1:${PORT}/health || exit 1'

# Start server and bind to Render's PORT
CMD sh -c 'uvicorn app.api:app --host 0.0.0.0 --port ${PORT}'
