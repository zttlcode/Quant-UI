# ============================================================
# Quant-UI Python Backend Dockerfile
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY api_server.py .
COPY src/ ./src/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

EXPOSE 8765

CMD ["python", "api_server.py"]
