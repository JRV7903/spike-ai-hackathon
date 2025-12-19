#!/bin/bash
set -e

# 1. Setup Environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# 2. Install Dependencies (Optimized with uv)
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install uv
    uv pip install -r requirements.txt
else
    echo "Error: requirements.txt not found"
    exit 1
fi

# 3. Start Server
echo "Starting server..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8080 > server.log 2>&1 &
PID=$!

# 4. Verify Startup
echo "Waiting for server to initialize..."
sleep 5

if ps -p $PID > /dev/null; then
    echo "Deployment successful. Server running on port 8080 (PID $PID)."
else
    echo "Deployment failed. Server exited immediately."
    echo "--- server.log ---"
    cat server.log
    exit 1
fi