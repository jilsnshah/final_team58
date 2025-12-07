FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for FAISS
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY pathway_reader.py .
COPY data_sync_service.py .
COPY app.py .
COPY aibot.py .
COPY frontend_actions.py .
COPY services/ ./services/

# Create output directory for vector store
RUN mkdir -p /app/carbon-intelligence/server/output

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV PORT=5000

# Run the application
CMD ["python", "app.py"]
