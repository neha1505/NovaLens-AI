FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy source code
COPY . /app

EXPOSE 8000

# Start FastAPI server
CMD ["python", "backend/main.py"]
