#!/bin/bash
# Debug script để kiểm tra tại sao events không hoạt động

echo "🔍 Debugging Frontend Events..."
echo ""

# 1. Check if backend is running
echo "1️⃣ Backend Status:"
if curl -s http://localhost:8862/health > /dev/null 2>&1; then
    echo "   ✅ Backend is running"
else
    echo "   ❌ Backend not responding"
    exit 1
fi

# 2. Check main page loads
echo ""
echo "2️⃣ Frontend Loading:"
MAIN_PAGE=$(curl -s http://localhost:8862/ | grep -o "IOC Agentic System" | head -1)
if [ -n "$MAIN_PAGE" ]; then
    echo "   ✅ Main page loads"
else
    echo "   ❌ Main page not loading"
fi

# 3. Check JavaScript files
echo ""
echo "3️⃣ JavaScript Files:"
JS_MAIN=$(curl -s http://localhost:8862/src/main.js | wc -l)
if [ "$JS_MAIN" -gt 10 ]; then
    echo "   ✅ main.js loaded ($JS_MAIN lines)"
else
    echo "   ❌ main.js not loading properly"
fi

# 4. Check API endpoints
echo ""
echo "4️⃣ API Endpoints:"
FUNCS=$(curl -s "http://localhost:8862/api/v1/registry/functions?limit=1" | grep -o '"total":[0-9]*' | grep -o '[0-9]*')
echo "   📦 Functions in DB: $FUNCS"

EXAMPLES=$(curl -s "http://localhost:8862/api/v1/query/examples" | grep -o "query" | wc -l)
echo "   📝 Example queries: $EXAMPLES"

# 5. Test query endpoint
echo ""
echo "5️⃣ Query Endpoint Test:"
QUERY_RESULT=$(curl -s -X POST http://localhost:8862/api/v1/query \
    -H "Content-Type: application/json" \
    -d '{"query":"test"}' | grep -o "query_id")

if [ -n "$QUERY_RESULT" ]; then
    echo "   ✅ Query endpoint working"
else
    echo "   ⚠️  Query endpoint response: (checking...)"
    curl -s -X POST http://localhost:8862/api/v1/query \
        -H "Content-Type: application/json" \
        -d '{"query":"test"}' | head -3
fi

echo ""
echo "="
echo "📋 Common Issues & Solutions:"
echo ""
echo "If clicks don't work on main page:"
echo "   1. Hard refresh browser: Ctrl+Shift+R (or Cmd+Shift+R)"
echo "   2. Clear browser cache: F12 > Application > Clear storage"
echo "   3. Check browser console (F12) for JavaScript errors"
echo "   4. Try test page: http://localhost:8862/test-events.html"
echo ""
echo "If test page doesn't load:"
echo "   curl http://localhost:8862/test-events.html"
echo ""
