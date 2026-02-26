#!/usr/bin/env bash
# Build script for Render deployment
# Installs Tesseract OCR system binary + Python dependencies

set -e  # Exit on error

echo "==> Installing system dependencies (Tesseract OCR + poppler)..."
apt-get update -qq
apt-get install -y tesseract-ocr tesseract-ocr-eng libglib2.0-0 libsm6 libxext6 libxrender-dev poppler-utils

echo "==> Tesseract version:"
tesseract --version

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Build complete!"
