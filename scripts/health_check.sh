#!/bin/bash
# System Verification Script

echo "🔍 IOC Agentic System - Health Check"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running
echo "📦 Checking Docker Containers..."
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Containers are running${NC}"
else
    echo -e "${RED}❌ Containers are not running${NC}"
    echo "Run: docker compose up -d"
    exit 1
fi

echo ""
echo "🔌 Checking Services..."

# Check Backend
if curl -s http://localhost:8862/health > /dev/null; then
    echo -e "${GREEN}✅ Backend API${NC} (http://localhost:8862)"
else
    echo -e "${RED}❌ Backend API not responding${NC}"
fi

# Check Frontend
if curl -s http://localhost:8862 | grep -q "IOC Agentic System"; then
    echo -e "${GREEN}✅ Frontend UI${NC} (http://localhost:8862)"
else
    echo -e "${RED}❌ Frontend not loading${NC}"
fi

# Check Database
FUNC_COUNT=$(curl -s "http://localhost:8862/api/v1/registry/functions?limit=1" | grep -o '"total":[0-9]*' | grep -o '[0-9]*')
if [ -n "$FUNC_COUNT" ]; then
    echo -e "${GREEN}✅ Database${NC} ($FUNC_COUNT functions registered)"
else
    echo -e "${RED}❌ Database connection issue${NC}"
fi

echo ""
echo "📊 API Endpoints..."

# Test key endpoints
ENDPOINTS=(
    "/health:Health"
    "/api/v1/registry/functions:Registry"
    "/api/v1/query/examples:Examples"
    "/api/v1/conversations:Conversations"
)

for endpoint in "${ENDPOINTS[@]}"; do
    IFS=':' read -r path name <<< "$endpoint"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8862$path")
    if [ "$STATUS" = "200" ]; then
        echo -e "${GREEN}✅${NC} $name ($path)"
    else
        echo -e "${RED}❌${NC} $name ($path) - HTTP $STATUS"
    fi
done

echo ""
echo "🌐 Access Points..."
echo "   🖥️  Main UI:     http://localhost:8862"
echo "   📚 API Docs:    http://localhost:8862/api/v1/docs"
echo "   🔧 Registry:    http://localhost:8862/#registry"
echo "   💬 Chat:        http://localhost:8862/#chat"

echo ""
echo "📝 Quick Commands..."
echo "   View logs:      docker compose logs backend --tail=50"
echo "   Restart:        docker compose restart"
echo "   Stop:           docker compose down"
echo "   Seed data:      bash scripts/quick_seed.sh"

echo ""
if [ "$FUNC_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ System is healthy and operational!${NC}"
else
    echo -e "${YELLOW}⚠️  System is running but database is empty${NC}"
    echo "Run: bash scripts/quick_seed.sh"
fi
