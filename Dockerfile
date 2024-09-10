# Use the official Python slim image
FROM python:3.11-slim

# Maintainer label
LABEL maintainer="Youssefwilliam"

# Prevent Python from writing .pyc files to disk
ENV PYTHONUNBUFFERED=1

# Set environment variable for the path
ENV PATH="/py/bin:$PATH"

# Create and set working directory
WORKDIR /app

# Copy requirements and app files
COPY ./requirements.txt /requirements.txt
COPY ./app /app

# Expose port 8000
EXPOSE 8000

ARG UNAME=app
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID -o $UNAME

# Install dependencies
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    /py/bin/pip install -r /requirements.txt && \
    apt-get purge -y --auto-remove gcc libpq-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --uid $UID --gid $GID --disabled-password --system --no-create-home $UNAME && \
    mkdir -p /vol/web/static && \
    mkdir -p /vol/web/media && \
    chown -R app:app /vol/web && \
    chmod -R 755 /vol/web

USER app


