FROM python:3.11-slim-bookworm

RUN mkdir /app
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_PROJECT_ENVIRONMENT=/usr/local

COPY README.md pyproject.toml uv.lock /app/
COPY cjdb /app/cjdb

RUN uv sync --frozen --no-group dev
