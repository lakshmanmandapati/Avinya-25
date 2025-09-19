# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy server directory (excluding sensitive files)
COPY server/ ./server/
COPY .env* ./

# Remove any accidentally copied credential files
RUN rm -f ./server/gcp_key.json ./server/*-key.json ./server/service-account*.json || true

# Create necessary directories and set permissions
RUN mkdir -p server/__pycache__ && \
    chmod -R 755 server/

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=server/proxy.py
ENV FLASK_ENV=production
ENV PORT=4000

# Expose port (Render uses PORT env variable)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Change to server directory and start the application
WORKDIR /app/server
CMD ["python", "proxy.py"]
