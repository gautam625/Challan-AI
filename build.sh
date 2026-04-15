#!/usr/bin/env bash

echo "Installing Tesseract..."

apt-get update -y
apt-get install -y tesseract-ocr tesseract-ocr-eng

echo "Tesseract version:"
tesseract --version

pip install -r requirements.txt
