FROM python:3.11-slim-buster
RUN apt-get update && \
    apt-get install

RUN mkdir /app
WORKDIR /app

ARG PIP_VERSION="pip==23.0.0"
ARG POETRY_VERSION="poetry==1.3.2"

RUN python3 -m pip install ${PIP_VERSION} ${POETRY_VERSION}

COPY README.md poetry.lock pyproject.toml /app/
COPY cjdb /app/cjdb

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --without dev