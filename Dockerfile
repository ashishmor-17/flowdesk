FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install uv
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen
ENV PATH="/app/.venv/bin:$PATH"

COPY . .

EXPOSE 8000
