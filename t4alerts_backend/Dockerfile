FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application code
# Context will be the root of the project
COPY . .

# Set python path to root
ENV PYTHONPATH=/app

# Expose port (internal)
EXPOSE 5000

# Run Gunicorn
# app:create_app() pattern
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "t4alerts_backend.app:create_app()", "--timeout", "120"]
