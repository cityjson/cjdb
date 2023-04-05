FROM python:3.8-slim-buster
# RUN apt-get update && \
#     apt-get install

RUN mkdir /app
WORKDIR /app

ARG PIP_VERSION="pip==22.3.0"
ARG SETUPTOOL_VERSION="setuptools==65.5.0"
ARG BUILD_VERSION="build==0.8.0"

RUN python3 -m pip install ${PIP_VERSION} ${SETUPTOOL_VERSION} ${BUILD_VERSION}

COPY README.md LICENSE changelog.md /app/
COPY model /app/model
COPY cjdb /app/cjdb

RUN python3 -m build 
RUN pip install dist/*.whl
