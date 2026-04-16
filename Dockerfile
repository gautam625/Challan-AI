# Use official Python slim image
FROM python:3.11-slim

# Install system dependencies: tesseract + opencv requirements
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY app.py .
COPY database.py .
COPY whatsapp.py .
COPY pdf.py .
COPY ocr.py .
COPY haarcascade_russian_plate_number.xml .

# Create a volume mount point for persistent DB storage
RUN mkdir -p /data
ENV DB_PATH=/data/cars.db

# Expose Streamlit port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
