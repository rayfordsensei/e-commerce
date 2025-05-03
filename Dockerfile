# syntax=docker/dockerfile:1

######################## Stage 0 – JS deps ########################
FROM node:20-alpine AS jsdeps
WORKDIR /app
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
RUN corepack enable   && \
    pnpm install --prod --frozen-lockfile  # only bootstrap

######################## Stage 1 – build ########################
FROM python:3.12-slim AS builder

# 1. Install build deps + uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

# 2. Copy static uv binary from Astral’s distroless layer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY --from=jsdeps /app/node_modules /app/node_modules

# 3. Enable non‑interactive uv & nicer logs
ENV UV_SYSTEM=true \
    PYTHONUNBUFFERED=1

# 4. Copy lock‑files first, resolve & cache dependencies
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"

# 5. Copy project source last
COPY . .

######################## Stage 2 – runtime ######################
FROM python:3.12-slim

# 6. Copy uv + site‑packages from the builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
WORKDIR /app

# 7. Provide default envs – all can be overridden at run‑time
COPY .env.example .env
ENV DEBUG=false \
    UV_SYSTEM=true \
    PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["uv", "run", "src/manage.py", "dev", "--host", "0.0.0.0"]
