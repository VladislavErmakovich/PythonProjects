# Используем Python 3.10 slim (легкий образ)
FROM python:3.10-slim

WORKDIR /src


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV PYTHONPATH=/src


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY seed.py .

EXPOSE 8000


CMD ["bash", "-c", "python seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]