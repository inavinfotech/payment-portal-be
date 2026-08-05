#!/bin/bash
# Script to run Alembic migrations

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run migrations
echo "Running database migrations..."
if [ -d "venv" ]; then
    ./venv/bin/python -m alembic upgrade head
else
    python3 -m alembic upgrade head
fi

if [ $? -eq 0 ]; then
    echo "Migrations completed successfully."
else
    echo "Migration failed. Please check the logs."
    exit 1
fi
