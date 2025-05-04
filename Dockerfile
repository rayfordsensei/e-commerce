# syntax=docker/dockerfile:1

######################## Stage 0 – JS deps ########################
FROM node:20-alpine AS jsdeps
WORKDIR /app
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
RUN corepack enable   && \
    pnpm install --prod --frozen-lockfile \
    && mkdir -p /assets/css /assets/js \
    && cp node_modules/bootstrap/dist/css/bootstrap.min.css /assets/css/ \
    && cp node_modules/bootstrap/dist/css/bootstrap.min.css.map /assets/css/ \
    && cp node_modules/bootstrap/dist/js/bootstrap.bundle.min.js /assets/js/ \
    && cp node_modules/bootstrap/dist/js/bootstrap.bundle.min.js.map /assets/js/

######################## Stage 1 – build ########################
FROM python:3.12-slim AS builder

# 1. Install build deps + uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates git && \
    rm -rf /var/lib/apt/lists/*

# 2. Copy static uv binary from Astral’s distroless layer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 3. Copy lock‑files first, resolve & cache dependencies
WORKDIR /app
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --locked \
    && rm -rf /root/.cache/pip

# 4. Copy project source last
COPY . .

######################## Stage 2 – runtime ######################
FROM python:3.12-slim

# 5. Copy uv + site‑packages from the builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ENV UV_PROJECT_ENVIRONMENT=/usr/local
ENV UV_SYSTEM_PYTHON=1

# 6. Provide default envs – all can be overridden at run‑time
COPY .env.example .env
ENV PYTHONUNBUFFERED=1
# ENV DEBUG=false  # doesn't seed user otherwise.

RUN mkdir -p /app/node_modules/bootstrap/dist
COPY --from=jsdeps /app/node_modules/bootstrap/dist /app/node_modules/bootstrap/dist

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "src/manage.py", "dev", "--host", "0.0.0.0"]
