FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      libpq-dev gcc libldap2-dev libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
