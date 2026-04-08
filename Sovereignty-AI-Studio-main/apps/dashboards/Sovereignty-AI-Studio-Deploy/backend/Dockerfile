FROM python:3.11-slim AS base

# No interactive shells, no history, no logs
ENV TERM=dumb \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Zero-trace install — only what burns
RUN apt-get update --no-cache \
    && apt-get install -y --no-install-recommends \
        gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    /tmp/* \
    /var/tmp/*

# Requirements — pinned, isolated, no global
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --force-reinstall -r requirements.txt && \
    pip cache purge

# App code — in last, no .git, no docs, no secrets
COPY . .

# No debug ports, no shells, no meta
EXPOSE 9898

# Run locked — single process, no fork, no shell
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9898"]