#!/bin/bash

# Exit immediately if any command exits with a non-zero status
set -e

echo "=== Starting Backend Deployment ==="

# Navigate to the backend directory (where this script is located)
cd "$(dirname "$0")"

# 1. Pull latest changes from dev branch
echo "Pulling latest changes from origin dev..."
git pull origin dev

# 2. Check and install python dependencies
if [ -f "requirements.txt" ]; then
    if [ -d "venv" ]; then
        echo "Checking and installing python packages..."
        ./venv/bin/pip install -r requirements.txt
    else
        echo "Warning: virtual environment not found, skipping package installation."
    fi
fi

# 3. Apply database migrations
if [ -f "./migrate.sh" ]; then
    echo "Running database migrations..."
    ./migrate.sh apply
else
    echo "Warning: migrate.sh not found, skipping database migrations."
fi

# 4. Restart the backend systemd service
SERVICE_NAME="payment-portal-be"
if [ -f ".env" ]; then
    ENV_SERVICE=$(grep -E '^(SERVICE_NAME|SYSTEMD_SERVICE_NAME|SERVICE)=' .env | head -n 1 | cut -d '=' -f2- | tr -d '"' | tr -d "'" | xargs 2>/dev/null || true)
    if [ -n "$ENV_SERVICE" ]; then
        SERVICE_NAME="$ENV_SERVICE"
    fi
fi

echo "Restarting backend service ($SERVICE_NAME)..."
sudo systemctl restart "$SERVICE_NAME"

echo "=== Backend Deployment Completed Successfully ==="
