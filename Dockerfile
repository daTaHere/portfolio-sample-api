FROM python:3.12-slim-bookworm

WORKDIR /api

RUN apt update && apt install -y 

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "run.py"]