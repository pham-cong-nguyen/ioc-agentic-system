#!/bin/bash
# Script để force reload frontend và clear cache

echo "🔄 Forcing frontend reload..."

# Thêm timestamp vào file để force reload
TIMESTAMP=$(date +%s)

# Touch các file JavaScript để browser reload
touch /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/src/main.js
touch /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/src/components/RegistryController.js

echo "✅ Files touched with new timestamp"
echo ""
echo "📋 Next steps:"
echo "   1. Open browser: http://localhost:8862"
echo "   2. Press Ctrl+Shift+R (Linux/Windows) or Cmd+Shift+R (Mac) to hard refresh"
echo "   3. Or press F12, right-click reload button, select 'Empty Cache and Hard Reload'"
echo ""
echo "🔍 Current status:"
echo "   Backend: http://localhost:8862/health"
curl -s http://localhost:8862/health | grep -q "ok" && echo "   ✅ Backend is healthy" || echo "   ❌ Backend not responding"

FUNC_COUNT=$(curl -s "http://localhost:8862/api/v1/registry/functions?limit=1" | grep -o '"total":[0-9]*' | grep -o '[0-9]*')
echo "   📦 Functions in DB: $FUNC_COUNT"
