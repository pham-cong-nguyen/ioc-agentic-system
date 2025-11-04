# 🚀 IOC Agentic System - Quick Start Guide

**Complete in 5 minutes!**

---

## Step 1: Prerequisites Check ✅

Make sure you have:
- ✅ Python 3.11+
- ✅ Docker & Docker Compose (recommended)
- ✅ LLM API Key (one of):
  - Google Gemini API Key ([Get it here](https://makersuite.google.com/app/apikey))
  - OpenAI API Key ([Get it here](https://platform.openai.com/api-keys))
  - Anthropic API Key ([Get it here](https://console.anthropic.com/))

---

## Step 2: Quick Setup 🔧

### Option A: Docker Compose (Recommended - 2 minutes)

```bash
# 1. Navigate to project
cd /home/ubuntu/nguyenpc2/2025/akaAPIs

# 2. Create environment file
cp .env.example .env

# 3. Edit .env and add your API key
nano .env
# Set: GOOGLE_API_KEY=your_actual_key_here

# 4. Start everything
docker-compose up -d

# 5. Initialize database
docker-compose exec backend python scripts/init_db.py

# 6. Done! ✨
```

### Option B: Using Makefile (Even Faster!)

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs

# One command to rule them all
make quickstart

# Then edit .env and add API key
nano .env

# Restart
make docker-down && make docker-up
```

### Option C: Interactive Setup Script

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs
./setup.sh
# Follow the interactive prompts
```

---

## Step 3: Access the System 🌐

Once started, access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:80 | Main user interface |
| **API Docs** | http://localhost:8862/api/v1/docs | Interactive API documentation |
| **Backend API** | http://localhost:8862 | REST API |
| **Health Check** | http://localhost:8862/health | System status |

---

## Step 4: First Query 💬

### Using the Frontend:
1. Open http://localhost:80
2. Click "Chat" tab
3. Type a query: `"Mức tiêu thụ điện hôm nay là bao nhiêu?"`
4. Press Enter

### Using the API:
```bash
# 1. Login first
curl -X POST http://localhost:8862/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Copy the access_token from response

# 2. Make a query
curl -X POST http://localhost:8862/api/v1/query \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the power consumption today?",
    "language": "en"
  }'
```

---

## Step 5: Explore Features 🎯

### Admin Panel (API Registry Management)
1. Go to http://localhost:80
2. Click "Configuration" tab
3. View, add, edit, or delete API functions
4. Import/export configurations as JSON

### Example Queries to Try

**Energy Domain:**
```
Vietnamese: "Mức tiêu thụ điện hôm nay là bao nhiêu?"
English: "What's the power consumption today?"
```

**Traffic Domain:**
```
Vietnamese: "So sánh lưu lượng giao thông tuần này với tuần trước"
English: "Compare this week's traffic with last week"
```

**Environment Domain:**
```
Vietnamese: "Chất lượng không khí ở Hà Nội như thế nào?"
English: "How's the air quality in Hanoi?"
```

**Analytics:**
```
Vietnamese: "Phân tích xu hướng tiêu thụ năng lượng tháng qua"
English: "Analyze energy consumption trend for the past month"
```

---

## 🔧 Common Commands

```bash
# View logs
docker-compose logs -f
# or
make docker-logs

# Restart services
docker-compose restart
# or
make docker-down && make docker-up

# Stop everything
docker-compose down
# or
make docker-down

# Reset database (WARNING: deletes all data)
make reset-db

# Check health
make health
```

---

## 📊 System Architecture Overview

```
┌─────────────────────────────────────┐
│     User Interface (Browser)        │
│  Chat Interface + Admin Panel       │
└───────────┬─────────────────────────┘
            │ HTTP REST
┌───────────┴─────────────────────────┐
│      FastAPI Backend (Port 8862)    │
│  ┌──────────────────────────┐       │
│  │  LangGraph Orchestrator  │       │
│  │  (Query Processing)      │       │
│  └──────────────────────────┘       │
│  Registry │ Executor │ Analyzer     │
└───────────┬─────────────────────────┘
            │
┌───────────┴─────────────────────────┐
│  PostgreSQL (5432) + Redis (6379)   │
└─────────────────────────────────────┘
```

---

## 🎓 How It Works

1. **User asks a question** in natural language (Vietnamese or English)

2. **LLM parses the query** to understand intent and extract entities
   - Intent: data_query, analytics, comparison, trend
   - Entities: time, location, metrics, etc.

3. **System searches** the Function Registry for relevant APIs

4. **LLM creates execution plan** by selecting appropriate functions

5. **APIs are called** (parallel or sequential)

6. **Results are analyzed** for insights and trends

7. **LLM generates response** in natural language

8. **User receives answer** with visualization suggestions

---

## 🔐 Security Note

**Default credentials are for demo only!**

For production:
1. Change `JWT_SECRET_KEY` in `.env`
2. Change `POSTGRES_PASSWORD` in `.env`
3. Implement proper user authentication
4. Use HTTPS
5. Configure firewall rules

---

## 📚 Next Steps

- **Read the full documentation:** [README.md](README.md)
- **Explore the API:** http://localhost:8862/api/v1/docs
- **Check architecture:** [documents/agentic_architecture.md](documents/agentic_architecture.md)
- **View project summary:** [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- **Contribute:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 🆘 Troubleshooting

### Services won't start
```bash
# Check if ports are already in use
sudo lsof -i :8862
sudo lsof -i :5432
sudo lsof -i :6379

# Clear and restart
docker-compose down -v
docker-compose up -d
```

### Database connection error
```bash
# Wait for PostgreSQL to be ready
docker-compose logs postgres

# Reinitialize database
docker-compose exec backend python scripts/init_db.py
```

### LLM not responding
- Check your API key in `.env`
- Verify `LLM_PROVIDER` is set correctly
- Check API quota/limits
- View backend logs: `docker-compose logs backend`

### Import errors
```bash
# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

---

## 💡 Tips

- **Save your queries**: The system tracks conversation history
- **Use the admin panel**: Easily manage API functions
- **Check examples**: Use `/query/examples` endpoint
- **Monitor performance**: Check processing time in responses
- **Leverage caching**: Repeated queries return faster

---

## 🎉 You're Ready!

The IOC Agentic System is now running and ready to process your queries!

**Happy querying! 🚀**
