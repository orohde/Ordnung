FROM python:3.13-slim

WORKDIR /app

# Text recognition for scanned pages (German + English)
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml VERSION README.md LICENSE ./
COPY src/ src/
COPY VERSION src/ordnung/VERSION
RUN pip install --no-cache-dir . && rm -rf src build

ENV ORDNUNG_ARCHIVE=/archiv \
    ORDNUNG_DATA=/data \
    ORDNUNG_PORT=8000 \
    OMP_THREAD_LIMIT=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD ["python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/version', timeout=5)"]

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["ordnung"]
