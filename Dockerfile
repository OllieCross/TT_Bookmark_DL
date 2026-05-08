FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY downloader.py .

# Output dirs created at runtime via volume mounts
VOLUME ["/app/TikTokVideos", "/app/TikTokImages"]

CMD ["python", "downloader.py"]
