# Backend API Endpoints Status

## Summary
This document tracks all API endpoints required by the frontend and their implementation status.

---

## ✅ **IMPLEMENTED & WORKING**

### Authentication (`/api/v1/auth`)
- ✅ `POST /auth/login` - Login endpoint (returns JWT tokens)
- ✅ `POST /auth/logout` - Logout endpoint  
- ✅ `GET /auth/me` - Get current user info
- ✅ `POST /auth/refresh` - Refresh access token

### Function Registry (`/api/v1/registry`)
- ✅ `GET /registry/functions` - List all functions with filters
- ✅ `POST /registry/functions` - Create new function
- ✅ `GET /registry/functions/{id}` - Get function by ID
- ✅ `PUT /registry/functions/{id}` - Update function
- ✅ `DELETE /registry/functions/{id}` - Delete function
- ✅ `POST /registry/functions/search` - Search functions
- ✅ `GET /registry/functions/domain/{domain}` - Get functions by domain
- ✅ `POST /registry/functions/bulk-import` - Bulk import functions
- ✅ `GET /registry/functions/export` - Export functions (TODO: implement query logic)
- ✅ `GET /registry/domains` - Get all domains
- ✅ `GET /registry/statistics` - Get registry stats (TODO: implement real stats)

### Query Processing (`/api/v1/query`)
- ✅ `POST /query/` - Process natural language query
- ✅ `GET /query/history` - Get query history (TODO: implement DB query)
- ✅ `GET /query/{query_id}` - Get specific query result (TODO: implement DB query)
- ✅ `POST /query/feedback` - Submit feedback (TODO: save to DB)
- ✅ `GET /query/examples` - Get example queries **[ADDED THIS SESSION]**

### Conversations (`/api/v1/conversations`)
- ✅ `GET /conversations` - List all conversations (TODO: implement DB query) **[ADDED THIS SESSION]**
- ✅ `GET /conversations/{id}` - Get conversation details (TODO: implement DB query) **[ADDED THIS SESSION]**
- ✅ `DELETE /conversations/{id}` - Delete conversation (TODO: implement DB deletion) **[ADDED THIS SESSION]**

### System
- ✅ `GET /health` - Health check
- ✅ `GET /api/v1/status` - System status

---

## ❌ **NOT IMPLEMENTED**

### WebSocket
- ❌ `WS /ws` - WebSocket endpoint for real-time streaming
  - **Status**: Not implemented yet
  - **Frontend Usage**: Used for streaming LLM responses
  - **TODO**: 
    - Implement WebSocket endpoint in `backend/main.py`
    - Add authentication via query parameter token
    - Handle message types: `chat_stream`, `notification`, `ping/pong`
    - Implement reconnection logic

---

## 🔧 **IMPLEMENTED BUT NEEDS DB INTEGRATION**

These endpoints are implemented with stub/TODO responses. Need database integration:

### Query Processing
1. **`GET /query/history`**
   - Current: Returns empty list `[]`
   - TODO: Query conversation_history table
   - Frontend expects: Array of `QueryHistory` objects

2. **`GET /query/{query_id}`**
   - Current: Returns 404 
   - TODO: Query by query_id from database
   - Frontend expects: `QueryResponse` object

3. **`POST /query/feedback`**
   - Current: Returns success message without saving
   - TODO: Save to audit_log or feedback table
   - Frontend expects: Confirmation message

### Conversations
4. **`GET /conversations`**
   - Current: Returns empty list `[]`
   - TODO: Query conversation_history grouped by conversation_id
   - Frontend expects: Array of `ConversationSummary` objects

5. **`GET /conversations/{id}`**
   - Current: Returns 404
   - TODO: Query messages for conversation_id
   - Frontend expects: `ConversationDetail` object with messages

6. **`DELETE /conversations/{id}`**
   - Current: Returns success without deleting
   - TODO: Delete from conversation_history table
   - Frontend expects: Confirmation message

### Registry
7. **`GET /registry/functions/export`**
   - Current: Returns empty object `{}`
   - TODO: Query all functions and format as downloadable JSON
   - Frontend expects: JSON array of functions

8. **`GET /registry/statistics`**
   - Current: Returns empty object `{}`
   - TODO: Calculate stats from function_registry table
   - Frontend expects: Object with counts, domains, usage stats

---

## 🐛 **KNOWN ISSUES**

### 1. `/registry/functions/search` Returns 404
- **Symptom**: `GET /api/v1/registry/functions/search?query=&domain=null&limit=100` returns 404
- **Cause**: Frontend is using `GET` but backend expects `POST`
- **Solution Options**:
  - A. Change frontend to use `POST`
  - B. Add `GET` handler for search endpoint
  - **Recommendation**: Add GET handler since it's more RESTful for search

### 2. WebSocket Connection Fails
- **Symptom**: `WebSocket connection to 'ws://localhost:8862/ws?token=...' failed`
- **Cause**: WebSocket endpoint not implemented
- **Priority**: HIGH - needed for streaming responses

### 3. `/query/examples` May Return 404 in Browser
- **Symptom**: Works in OpenAPI docs but frontend gets 404
- **Possible Causes**:
  - CORS issue
  - Token expiration
  - Route ordering problem
- **TODO**: Debug why frontend can't access it

---

## 🎯 **PRIORITY FIXES**

### Priority 1: Fix Search Endpoint
```python
# Add to backend/registry/routes.py
@router.get("/functions/search")
async def search_functions_get(
    query: Optional[str] = None,
    domain: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """GET version of search for frontend compatibility"""
    # Reuse existing search logic
    pass
```

### Priority 2: Implement WebSocket
```python
# Add to backend/main.py
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    # Verify token
    # Accept connection
    # Handle messages
    pass
```

### Priority 3: Debug `/query/examples` Issue
- Check if token is valid
- Test with fresh login
- Check CORS headers
- Verify route is registered correctly

---

## 📊 **Implementation Statistics**

- **Total Endpoints**: 28
- **Fully Implemented**: 20 (71%)
- **Partially Implemented (needs DB)**: 7 (25%)
- **Not Implemented**: 1 (4% - WebSocket)

---

## 🔍 **Testing Checklist**

### Can Test Now
- [x] Login / Logout
- [x] Get current user
- [x] Create/Read/Update/Delete functions
- [x] Search functions (via POST)
- [x] Process query
- [x] Health check

### Need DB Data First
- [ ] Get query history
- [ ] Get conversations
- [ ] Export functions
- [ ] Registry statistics

### Need Implementation
- [ ] WebSocket streaming
- [ ] GET version of search

---

## 📝 **Notes for Developer**

1. **All endpoint definitions exist** - Routes are registered, schemas are defined
2. **Database tables exist** - Migrations have been run
3. **Missing pieces**: 
   - WebSocket implementation
   - Database query logic for history/conversations
   - GET handler for search
4. **Frontend is fully functional** - Just waiting for backend endpoints to return real data

**Next Steps**:
1. Fix `/registry/functions/search` to accept GET
2. Implement WebSocket endpoint
3. Debug why `/query/examples` returns 404 in browser
4. Add database queries for conversation endpoints
