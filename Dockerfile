FROM python:3.12.2-slim

LABEL version="1.0"
LABEL description="Base image for vegetation index analysis"

# Install OS and build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev \
        python3-gdal \
        gcc \
        g++ \
        libfreetype6-dev \
        libpng-dev && \
    pip install --no-cache-dir \
        numpy \
        rasterio \
        matplotlib && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
