FROM python:3.12-slim-bookworm

WORKDIR /api

RUN apt update && apt upgrade -y && apt autoclean -y

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

# Possible security improvement: run as non-root user for production
# RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /api
# USER appuser

EXPOSE 5000

CMD ["python", "run.py"]