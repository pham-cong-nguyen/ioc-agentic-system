#!/bin/bash
# Quick script to install new dependencies and restart backend

set -e  # Exit on error

echo "🔄 Installing new dependencies and restarting backend..."
echo ""

# Get current directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Install dependencies
echo "📦 Step 1: Installing Python dependencies..."
cd "$DIR"
pip install -r backend/requirements.txt
echo "✅ Dependencies installed"
echo ""

# Step 2: Kill existing backend process
echo "🔪 Step 2: Stopping existing backend..."
pkill -f "uvicorn backend.main:app" || echo "No backend process running"
sleep 2
echo "✅ Backend stopped"
echo ""

# Step 3: Start backend
echo "🚀 Step 3: Starting backend server..."
nohup python -m uvicorn backend.main:app --host 0.0.0.0 --port 8862 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
echo ""

# Step 4: Wait for health check
echo "⏳ Step 4: Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -f http://localhost:8862/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Step 5: Show status
echo "📊 Step 5: Service status:"
echo "Backend: http://localhost:8862"
echo "Health: http://localhost:8862/health"
echo "API Docs: http://localhost:8862/docs"
echo ""
echo "📋 To view logs: tail -f backend.log"
echo "🛑 To stop backend: pkill -f 'uvicorn backend.main:app'"
