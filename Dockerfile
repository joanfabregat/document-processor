# Copyright (c) 2025 Joan Fabrégat <j@fabreg.at>
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, subject to the conditions in the full MIT License.
# The Software is provided "as is", without warranty of any kind.

ARG PYTHON_VERSION=3.12


# --- Builder Image ---
FROM python:${PYTHON_VERSION}-slim AS builder

WORKDIR /src

# Install uv and its dependencies
COPY --from=ghcr.io/astral-sh/uv:0.6.8 /uv /uvx /bin/
RUN chmod +x /bin/uv /bin/uvx && \
    uv venv .venv
ENV PATH="/src/.venv/bin:$PATH"

# Copy dependency specification and install production dependencies
COPY uv.lock pyproject.toml ./
RUN uv sync --frozen


# --- Final Image ---
FROM python:${PYTHON_VERSION}-slim AS final

ARG PORT=8000
ARG VERSION
ARG BUILD_ID
ARG COMMIT_SHA

ENV PORT=${PORT}
ENV VERSION=${VERSION}
ENV BUILD_ID=${BUILD_ID}
ENV COMMIT_SHA=${COMMIT_SHA}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/src/.cache/huggingface
ENV DOCLING_MODELS=${HF_HOME}

WORKDIR /src
ENV HOME=/src

# Config for Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    tesseract-ocr-deu \
    tesseract-ocr-spa \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application
RUN addgroup --system app && \
    adduser --system --group --no-create-home app && \
    chown app:app /src

# Copy the virtual environment
COPY --from=builder --chown=app:app /src/.venv .venv
ENV PATH="/src/.venv/bin:$PATH"

# create a cache directory for docling models
RUN mkdir -p ${DOCLING_MODELS} && \
    chown -R app:app ${DOCLING_MODELS}

# Copy the application code
COPY --chown=app:app app/ ./app

# Ensure a non-root user
USER app:app

# Download docling models
RUN docling-tools models download layout --force --output-dir=${DOCLING_MODELS} && \
    docling-tools models download tableformer --force --output-dir=${DOCLING_MODELS}

EXPOSE $PORT
CMD ["sh", "-c", "uvicorn app.api:api --host 0.0.0.0 --port $PORT --workers 1 --log-level info --timeout-keep-alive 0"]

