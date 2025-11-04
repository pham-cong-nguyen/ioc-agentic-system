# 🎉 IOC Agentic System - Đã Chạy Thành Công!

## ✅ Services Đang Chạy

| Service | Container | Port | URL | Trạng thái |
|---------|-----------|------|-----|------------|
| **Backend API** | ioc-backend | 8862 | http://localhost:8862 | ✅ Running |
| **Frontend** | ioc-frontend | 3450 | http://localhost:3450 | ✅ Running |
| **PostgreSQL** | ioc-postgres | 5432 | localhost:5432 | ✅ Healthy |
| **Redis** | ioc-redis | 15379 | localhost:15379 | ✅ Healthy |

---

## 🌐 Truy Cập Ứng Dụng

### Frontend (Giao diện người dùng)

```
http://localhost:3450      # Frontend development server
http://localhost:8862      # Frontend served by backend
```

**Chọn một trong hai đều được!**

### Backend API

```
http://localhost:8862              # API endpoint
http://localhost:8862/api/v1/docs  # Swagger UI documentation
http://localhost:8862/api/v1/redoc # ReDoc documentation
http://localhost:8862/health       # Health check
```

---

## 🎨 Giao Diện Frontend

Khi truy cập, bạn sẽ thấy:

- ✅ **Sidebar bên trái** với menu:
  - 💬 Chat Interface
  - 🗄️ API Registry
  - 📊 Analytics
  - ⚙️ Settings

- ✅ **Top bar** với:
  - 🔍 Search box
  - 🌓 Theme toggle (Dark/Light)
  - 🔔 Notifications

- ✅ **Chat interface** với:
  - Welcome message
  - Example queries (tiếng Việt)
  - Message input area

- ✅ **Dark theme** với gradient xanh-tím (LumiAI style)

---

## 🔧 Kiểm Tra Hoạt Động

### 1. Test Backend Health

```bash
curl http://localhost:8862/health
```

**Kết quả mong đợi:**
```json
{
  "status": "healthy",
  "service": "IOC Agentic System",
  "version": "1.0.0"
}
```

### 2. Test Frontend

Mở trình duyệt:
```
http://localhost:3450
```

Bạn sẽ thấy giao diện chat với dark theme.

### 3. Test API Documentation

```
http://localhost:8862/api/v1/docs
```

Swagger UI với tất cả endpoints.

---

## 📝 Các Lệnh Hữu Ích

### Xem logs

```bash
# Xem logs tất cả services
docker compose logs -f

# Xem logs backend only
docker compose logs -f backend

# Xem logs frontend only
docker compose logs -f frontend

# Xem 100 dòng cuối
docker compose logs --tail=100 backend
```

### Restart services

```bash
# Restart tất cả
docker compose restart

# Restart backend only
docker compose restart backend

# Restart frontend only
docker compose restart frontend
```

### Dừng services

```bash
# Dừng tất cả (giữ data)
docker compose stop

# Dừng và xóa containers (giữ data)
docker compose down

# Xóa cả data (⚠️ NGUY HIỂM)
docker compose down -v
```

### Xem trạng thái

```bash
# Xem containers đang chạy
docker compose ps

# Xem resource usage (CPU, RAM)
docker stats

# Xem networks
docker network ls
```

---

## 🚀 Sử Dụng Chat

### 1. Mở frontend

```
http://localhost:3450
```

### 2. Thử các example queries

Click vào các example queries để test:

- ✅ **"Mức tiêu thụ điện hôm nay là bao nhiêu?"**
- ✅ **"So sánh lưu lượng giao thông tuần này với tuần trước"**
- ✅ **"Chất lượng không khí ở Hà Nội như thế nào?"**

### 3. Hoặc nhập câu hỏi tùy ý

Hệ thống hỗ trợ:
- ✅ Tiếng Việt
- ✅ English
- ✅ Auto-detect language

---

## 🔌 API Endpoints Quan Trọng

### Authentication

```bash
# Login
POST http://localhost:8862/api/v1/auth/login
{
  "username": "admin",
  "password": "password"
}

# Get current user
GET http://localhost:8862/api/v1/auth/me
Authorization: Bearer <token>
```

### Chat/Query

```bash
# Process query
POST http://localhost:8862/api/v1/query/process
{
  "query": "Mức tiêu thụ điện hôm nay?",
  "language": "vi"
}
```

### Function Registry

```bash
# List functions
GET http://localhost:8862/api/v1/registry/functions

# Add function
POST http://localhost:8862/api/v1/registry/functions
{
  "name": "get_power_consumption",
  "domain": "energy",
  ...
}
```

---

## 🗄️ Database Access

### Connect to PostgreSQL

```bash
# From host machine
psql -h localhost -p 5432 -U ioc_user -d ioc_db
# Password: ioc_password_secure_2025

# From Docker
docker compose exec postgres psql -U ioc_user -d ioc_db
```

### Common queries

```sql
-- List all tables
\dt

-- Show function registry
SELECT * FROM api_functions;

-- Show users
SELECT * FROM users;
```

### Connect to Redis

```bash
# From Docker
docker compose exec redis redis-cli

# From host (if redis-cli installed)
redis-cli -p 15379
```

---

## 📊 Monitoring

### Check container health

```bash
# All containers
docker compose ps

# Detailed health status
docker inspect ioc-backend --format='{{.State.Health.Status}}'
docker inspect ioc-postgres --format='{{.State.Health.Status}}'
docker inspect ioc-redis --format='{{.State.Health.Status}}'
```

### Resource usage

```bash
# Real-time stats
docker stats ioc-backend ioc-frontend ioc-postgres ioc-redis

# Disk usage
docker system df
```

---

## 🐛 Troubleshooting

### Frontend không hiển thị

1. Kiểm tra frontend đang chạy:
   ```bash
   docker compose ps frontend
   ```

2. Xem logs:
   ```bash
   docker compose logs frontend
   ```

3. Restart:
   ```bash
   docker compose restart frontend
   ```

### Backend API không response

1. Check logs:
   ```bash
   docker compose logs backend
   ```

2. Check database connection:
   ```bash
   docker compose exec backend python -c "from backend.utils.database import engine; print(engine)"
   ```

3. Restart backend:
   ```bash
   docker compose restart backend
   ```

### Database connection error

1. Check postgres is running:
   ```bash
   docker compose ps postgres
   ```

2. Test connection:
   ```bash
   docker compose exec postgres pg_isready -U ioc_user -d ioc_db
   ```

3. Check credentials in .env:
   ```bash
   cat .env | grep POSTGRES
   ```

---

## 🔐 Security Notes

**⚠️ QUAN TRỌNG cho Production:**

1. **Đổi JWT_SECRET_KEY:**
   ```bash
   # Tạo secret key mới
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   
   # Cập nhật trong .env
   JWT_SECRET_KEY=<key_mới>
   ```

2. **Đổi POSTGRES_PASSWORD:**
   ```bash
   # Cập nhật trong .env
   POSTGRES_PASSWORD=<password_mạnh>
   ```

3. **Set DEBUG=false:**
   ```bash
   DEBUG=false
   ```

4. **Cấu hình CORS đúng:**
   ```bash
   CORS_ORIGINS=https://yourdomain.com
   ```

---

## 📚 Documentation

- **API Docs:** http://localhost:8862/api/v1/docs
- **Quick Start:** `QUICKSTART.md`
- **Docker Guide:** `DOCKER_COMPOSE_GUIDE.md`
- **Frontend Only:** `FRONTEND_ONLY_GUIDE.md`
- **Change Port:** `CHANGE_PORT.md`

---

## 🎯 Next Steps

1. **Thử chat với LLM:**
   - Mở http://localhost:3450
   - Gõ câu hỏi tiếng Việt
   - Xem response

2. **Quản lý functions:**
   - Vào Registry view
   - Thêm/sửa/xóa functions
   - Import/Export JSON

3. **Xem Analytics:**
   - Vào Analytics view
   - Xem stats và charts
   - Monitor usage

4. **Cấu hình Settings:**
   - Vào Settings view
   - Đổi theme, language
   - Export/import data

---

## 🎉 Hoàn Tất!

Hệ thống đã sẵn sàng sử dụng với:

- ✅ Backend API running on port 8862
- ✅ Frontend UI running on port 3450
- ✅ PostgreSQL database ready
- ✅ Redis cache ready
- ✅ LLM integration configured (OpenAI)
- ✅ Dark theme enabled
- ✅ Vietnamese language supported

**Chúc bạn phát triển vui vẻ! 🚀**

---

## 📞 Support

Nếu gặp vấn đề:

1. Check logs: `docker compose logs -f`
2. Check this file: `RUNNING_SYSTEM.md`
3. Check guides in docs/
4. Restart: `docker compose restart`

**Happy Coding! 💻✨**
