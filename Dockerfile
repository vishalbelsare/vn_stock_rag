# Dockerfile

FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    ca-certificates \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /build/requirements.txt
RUN python -m pip install --upgrade pip wheel setuptools && \
    pip wheel --no-cache-dir --wheel-dir /wheels -r /build/requirements.txt

FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN addgroup --system app && \
    adduser --system --ingroup app --home /home/app --shell /bin/bash app && \
    mkdir -p /home/app && chown -R app:app /home/app

ENV HOME=/home/app
ENV XDG_DATA_HOME=/home/app/.local/share
ENV XDG_CONFIG_HOME=/home/app/.config
ENV XDG_CACHE_HOME=/home/app/.cache
RUN mkdir -p ${XDG_DATA_HOME} ${XDG_CONFIG_HOME} ${XDG_CACHE_HOME} && chown -R app:app /home/app

WORKDIR /home/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    xz-utils \
    libxrender1 \
    libfontconfig1 \
    libxext6 \
    libjpeg62-turbo \
    libgtk-3-0 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

RUN set -e; \
    for pair in "0.12.6.1-3 bookworm" "0.12.6.1-2 bullseye"; do \
      set -- $pair; TAG=$1; OSNAME=$2; \
      URL="https://github.com/wkhtmltopdf/packaging/releases/download/${TAG}/wkhtmltox_${TAG}.${OSNAME}_amd64.deb"; \
      echo "Attempting to fetch $URL"; \
      if wget -q --spider "$URL"; then \
        echo "Found $URL - downloading"; \
        wget -O /tmp/wkhtmltox.deb "$URL"; \
        break; \
      else \
        echo "Not found: $URL"; \
      fi; \
    done; \
    if [ -f /tmp/wkhtmltox.deb ]; then \
      dpkg -i /tmp/wkhtmltox.deb || true; \
      apt-get update && apt-get install -f -y; \
      rm -f /tmp/wkhtmltox.deb; \
    else \
      echo "WARNING: wkhtmltopdf package not downloaded. If you need wkhtmltopdf, set a valid TAG/OS or check releases."; \
    fi

COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*

ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY . /home/app

RUN chown -R app:app /home/app

USER app

CMD ["python", "api.py"]
