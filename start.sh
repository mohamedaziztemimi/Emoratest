#!/bin/bash
# EmoraTest V1 — Quick Start
# Usage: bash start.sh
#
# Prerequisites: Docker + Docker Compose OR Python 3.11+ & Node 20+

set -e

echo "============================================"
echo "  EmoraTest V1 — Starting up..."
echo "============================================"

# Option 1: Docker Compose (recommended)
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo "[1/3] Starting services with Docker Compose..."
    docker compose up -d --build

    echo "[2/3] Waiting for database..."
    sleep 5

    echo "[3/3] Running migrations..."
    docker compose exec backend alembic upgrade head

    echo ""
    echo "============================================"
    echo "  EmoraTest V1 is running!"
    echo ""
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/api/v1/docs"
    echo "============================================"
    exit 0
fi

# Option 2: Local development
echo "[1/4] Starting backend..."
cd backend
pip install -e ".[dev]" > /dev/null 2>&1
echo "[2/4] Running migrations..."
alembic upgrade head 2>/dev/null || echo "  (migrations may already be applied)"
echo "[3/4] Starting backend server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

echo "[4/4] Starting frontend..."
cd frontend
npm install > /dev/null 2>&1
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================"
echo "  EmoraTest V1 is running!"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/api/v1/docs"
echo ""
echo "  Press Ctrl+C to stop"
echo "============================================"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
