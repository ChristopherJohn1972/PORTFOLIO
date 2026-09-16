#!/bin/bash
# Portfolio Backend — WSL/Linux Startup Script
# Run from portfolio-api directory

set -e

VENV_DIR="./venv"
PORT=${1:-8000}

echo "=== Portfolio Backend Startup ==="

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Run migrations
echo "Running migrations..."
python manage.py migrate --run-syncdb 2>/dev/null || python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

# Start server
echo "Starting server on port $PORT..."
echo "Dashboard: http://127.0.0.1:$PORT/dashboard/"
echo "API: http://127.0.0.1:$PORT/api/"
echo ""
python manage.py runserver 0.0.0.0:$PORT
