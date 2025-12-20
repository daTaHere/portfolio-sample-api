FROM python:3.12-slim-bookworm

WORKDIR /api

RUN apt update \
    && apt upgrade -y --no-install-recommends \
    && apt autoremove -y \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Security improvement: run as non-root user for production
# For this demo, we keep root to simplify container startup

EXPOSE 5000

CMD ["python", "run.py"]