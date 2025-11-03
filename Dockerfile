# Dockerfile

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libgtk-3-0 \
    libpango-1.0-0 \
    libcairo2 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


FROM python:3.12-slim

RUN addgroup --system app && adduser --system --group app

COPY --from=builder / /

COPY --from=builder /wheels /wheels

RUN pip install --no-cache /wheels/*

WORKDIR /home/app
COPY . .

RUN chown -R app:app /home/app

USER app