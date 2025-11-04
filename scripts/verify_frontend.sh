#!/bin/bash
# Force clear và reload frontend

echo "🔄 FORCING FRONTEND RELOAD..."
echo ""

# 1. Touch files to update timestamp
echo "1️⃣ Updating file timestamps..."
touch /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/index.html
touch /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/src/main.js
touch /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/src/services/api.js
echo "   ✅ Files touched"

# 2. Verify files
echo ""
echo "2️⃣ Verifying files..."
if [ -f "/home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/index.html" ]; then
    LINES=$(wc -l < /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/index.html)
    echo "   ✅ index.html: $LINES lines"
else
    echo "   ❌ index.html NOT FOUND"
fi

if [ -f "/home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/src/main.js" ]; then
    LINES=$(wc -l < /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/src/main.js)
    echo "   ✅ main.js: $LINES lines"
else
    echo "   ❌ main.js NOT FOUND"
fi

# 3. Check backend serving
echo ""
echo "3️⃣ Testing backend serving..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8862/)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Backend serving index.html (HTTP $HTTP_CODE)"
else
    echo "   ❌ Backend error (HTTP $HTTP_CODE)"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8862/src/main.js)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Backend serving main.js (HTTP $HTTP_CODE)"
else
    echo "   ❌ Backend error (HTTP $HTTP_CODE)"
fi

# 4. Instructions
echo ""
echo "="
echo "📋 NEXT STEPS:"
echo ""
echo "1. Open browser in INCOGNITO mode: Ctrl+Shift+N"
echo "2. Go to: http://localhost:8862"
echo "3. Press F12 to open Console"
echo "4. Look for these logs:"
echo "   - '🔍 INDEX.HTML LOADED' (should appear FIRST)"
echo "   - '🚀 main.js LOADING...' (should appear after)"
echo "   - '✅ DOMContentLoaded fired!' (should appear last)"
echo ""
echo "5. If you see all 3 logs → JavaScript is working!"
echo "6. If you only see first log → main.js not loading"
echo "7. If you see NO logs → browser cache issue"
echo ""
echo "="
echo ""
echo "💡 If still not working:"
echo "   - Close ALL browser windows"
echo "   - Clear browser cache completely"
echo "   - Open fresh incognito window"
echo ""
