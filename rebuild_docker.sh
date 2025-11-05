#!/bin/bash
# Script to rebuild Docker containers with new dependencies

set -e  # Exit on error

echo "🔄 Rebuilding Docker containers with new dependencies..."
echo ""

# Step 1: Stop running containers
echo "📦 Step 1: Stopping running containers..."
docker-compose down
echo "✅ Containers stopped"
echo ""

# Step 2: Remove old backend image
echo "🗑️  Step 2: Removing old backend image..."
docker rmi akaapis-backend 2>/dev/null || echo "No old image to remove"
echo "✅ Old image removed"
echo ""

# Step 3: Build new backend image
echo "🔨 Step 3: Building new backend image with dependencies..."
docker-compose build backend --no-cache
echo "✅ Backend image built"
echo ""

# Step 4: Start services
echo "🚀 Step 4: Starting services..."
docker-compose up -d postgres redis
echo "⏳ Waiting for database to be ready..."
sleep 10

docker-compose up -d backend
echo "✅ Services started"
echo ""

# Step 5: Check health
echo "🏥 Step 5: Checking service health..."
sleep 5
docker-compose ps
echo ""

# Step 6: Show logs
echo "📋 Step 6: Showing backend logs (Ctrl+C to exit)..."
echo ""
docker-compose logs -f backend
