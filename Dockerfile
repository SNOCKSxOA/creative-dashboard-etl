FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Cloud Run expects the app to listen on PORT (default 8080)
ENV PORT=8080
ENV PYTHONPATH=/app/src

# Use gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 2 --timeout 540 src.main:app
