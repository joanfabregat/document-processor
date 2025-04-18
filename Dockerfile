# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.


##
# Base Image
##
FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04 AS base
#FROM nvidia/cuda:12.8.1-devel-ubuntu24.04 AS base

WORKDIR /src
ENV HOME=/src

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Paris
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"


# Install Python and necessary dependencies
RUN apt-get update  \
    && apt-get install -y \
        python3.12 \
        python3.12-dev \
        #curl \
        git \
        #build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a symbolic link for python3 to python3.10
RUN ln -sf /usr/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/bin/python3 /usr/bin/python

##
# Builder Image
##
FROM base AS builder

# Install uv and its dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN chmod +x /bin/uv /bin/uvx
RUN uv venv .venv
ENV PATH="/src/.venv/bin:$PATH"

# Copy dependency specification and install production dependencies
COPY uv.lock pyproject.toml ./
RUN uv sync --frozen


##
# Final Image
##
FROM base AS final

ARG PORT=8000
ARG VERSION
ARG BUILD_ID
ARG COMMIT_SHA

ENV PORT=${PORT}
ENV VERSION=${VERSION}
ENV BUILD_ID=${BUILD_ID}
ENV COMMIT_SHA=${COMMIT_SHA}

ENV HF_HOME=/src/.cache/huggingface
ENV DOCLING_MODELS=${HF_HOME}
ENV EASYOCR_MODULE_PATH=/src/.cache/easyocr

# Create a non-root user to run the application
RUN addgroup --system app && \
    adduser --system --group --no-create-home app && \
    chown app:app /src

# Copy the virtual environment
COPY --from=builder --chown=app:app /src/.venv /src/.venv
ENV PATH="/src/.venv/bin:$PATH"

# Copy the application code
COPY --chown=app:app app/ /src/app

# Ensure a non-root user
USER app:app

# Download Docling and EasyOCR models
RUN mkdir -p ${HF_HOME} && \
    mkdir -p ${EASYOCR_MODULE_PATH} && \
    python -m app.download_models

EXPOSE $PORT
CMD ["sh", "-c", "uvicorn app.api:api --host 0.0.0.0 --port $PORT --workers 1 --log-level info --timeout-keep-alive 0"]

