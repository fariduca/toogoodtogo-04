#!/usr/bin/env pwsh
# Convenience launcher for the Telegram Marketplace Bot

$ErrorActionPreference = "Stop"

Write-Host "Starting Telegram Marketplace Bot..." -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
} else {
    .\.venv\Scripts\Activate.ps1
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Warning ".env file not found. Copy .env.example and configure it."
    exit 1
}

# Run the bot
python src/bot/run.py
