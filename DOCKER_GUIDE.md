# 🐳 Hướng Dẫn Chạy IOC Agentic System với Docker Compose

Tài liệu này hướng dẫn chi tiết cách chạy cả Frontend và Backend bằng Docker Compose.

---

## 📋 Yêu Cầu Hệ Thống

- **Docker**: Version 20.10 trở lên
- **Docker Compose**: Version 2.0 trở lên
- **RAM**: Tối thiểu 4GB (Khuyến nghị 8GB)
- **Disk Space**: Tối thiểu 10GB

### Kiểm tra Docker đã cài đặt:

```bash
docker --version
docker-compose --version
```

Nếu chưa có Docker, tham khảo: https://docs.docker.com/get-docker/

---

## 🚀 Bước 1: Chuẩn Bị

### 1.1. Clone hoặc vào thư mục project

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs
```

### 1.2. Tạo file .env

```bash
# Copy file .env.example thành .env
cp .env.example .env

# Chỉnh sửa file .env với editor yêu thích
nano .env
```

**Các biến quan trọng cần cấu hình trong .env:**

```env
# LLM Provider - Chọn một trong các options
LLM_PROVIDER=gemini

# Google Gemini API Key (BẮT BUỘC nếu dùng Gemini)
GOOGLE_API_KEY=AIzaSy...your-key-here

# Hoặc OpenAI
# OPENAI_API_KEY=sk-...your-key-here

# Database (Giữ mặc định hoặc thay đổi)
POSTGRES_USER=ioc_user
POSTGRES_PASSWORD=ioc_password_strong_123
POSTGRES_DB=ioc_db

# JWT Secret (ĐỔI MẬT KHẨU MẠNH CHO PRODUCTION!)
JWT_SECRET_KEY=change-this-to-strong-random-string-in-production
```

### 1.3. Kiểm tra cấu trúc thư mục

```bash
ls -la
```

Đảm bảo có các file/folder sau:
- ✅ `docker-compose.yml`
- ✅ `Dockerfile`
- ✅ `backend/`
- ✅ `frontend/`
- ✅ `.env`

---

## 🎯 Bước 2: Chạy với Docker Compose

### Option 1: Chế độ Development (Đơn giản nhất - Chỉ Backend)

Backend sẽ serve cả frontend static files:

```bash
# Khởi động tất cả services
docker-compose up -d

# Xem logs
docker-compose logs -f backend
```

**Truy cập:**
- 🌐 Frontend: http://localhost:8862
- 🔌 Backend API: http://localhost:8862/api/v1/docs
- ❤️ Health Check: http://localhost:8862/health

### Option 2: Chế độ Development với Frontend riêng

Frontend chạy trên port 3000 với live reload:

```bash
# Khởi động với profile dev
docker-compose --profile dev up -d

# Xem logs
docker-compose logs -f
```

**Truy cập:**
- 🌐 Frontend: http://localhost:3000
- 🔌 Backend API: http://localhost:8862/api/v1/docs

### Option 3: Chế độ Production với Nginx

Nginx sẽ serve frontend và proxy backend:

```bash
# Khởi động với profile production
docker-compose --profile production up -d

# Xem logs
docker-compose logs -f nginx
```

**Truy cập:**
- 🌐 Frontend + Backend: http://localhost (port 80)

---

## 📊 Bước 3: Quản Lý Containers

### Xem trạng thái containers

```bash
docker-compose ps
```

### Xem logs của từng service

```bash
# Backend logs
docker-compose logs -f backend

# Database logs
docker-compose logs -f postgres

# Redis logs
docker-compose logs -f redis

# Tất cả logs
docker-compose logs -f
```

### Khởi động lại một service cụ thể

```bash
# Restart backend
docker-compose restart backend

# Restart tất cả
docker-compose restart
```

### Dừng và xóa containers

```bash
# Dừng tất cả
docker-compose stop

# Dừng và xóa containers (giữ data)
docker-compose down

# Dừng, xóa containers VÀ XÓA DATA (⚠️ Cẩn thận!)
docker-compose down -v
```

---

## 🔧 Bước 4: Troubleshooting (Xử lý lỗi)

### Lỗi: Port đã được sử dụng

```bash
# Kiểm tra port 8862
sudo lsof -i :8862

# Kill process đang dùng port
sudo kill -9 <PID>

# Hoặc thay đổi port trong .env
PORT=8080
```

### Lỗi: Database connection failed

```bash
# Kiểm tra PostgreSQL đã chạy chưa
docker-compose ps postgres

# Xem logs PostgreSQL
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Vào PostgreSQL để debug
docker-compose exec postgres psql -U ioc_user -d ioc_db
```

### Lỗi: Redis connection failed

```bash
# Kiểm tra Redis
docker-compose ps redis

# Test Redis
docker-compose exec redis redis-cli ping
# Kết quả mong đợi: PONG
```

### Lỗi: LLM API Key không hợp lệ

```bash
# Kiểm tra biến môi trường
docker-compose exec backend env | grep API_KEY

# Nếu sai, sửa file .env rồi restart
docker-compose restart backend
```

### Rebuild containers sau khi thay đổi code

```bash
# Rebuild và restart
docker-compose up -d --build

# Force rebuild không dùng cache
docker-compose build --no-cache
docker-compose up -d
```

### Xem resource usage

```bash
# CPU, RAM usage
docker stats

# Disk usage
docker system df
```

---

## 🗄️ Bước 5: Quản Lý Database

### Khởi tạo database (chạy migrations)

```bash
# Vào container backend
docker-compose exec backend bash

# Chạy init script
python scripts/init_db.py

# Thoát
exit
```

### Backup database

```bash
# Backup
docker-compose exec postgres pg_dump -U ioc_user ioc_db > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U ioc_user ioc_db < backup_20250103.sql
```

### Truy cập PostgreSQL CLI

```bash
docker-compose exec postgres psql -U ioc_user -d ioc_db
```

Các lệnh SQL hữu ích:
```sql
-- Liệt kê tables
\dt

-- Xem structure của table
\d api_functions

-- Query data
SELECT * FROM api_functions LIMIT 10;

-- Thoát
\q
```

---

## 🧪 Bước 6: Testing

### Test Backend API

```bash
# Health check
curl http://localhost:8862/health

# Login (lấy token)
curl -X POST http://localhost:8862/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Test query
curl -X POST http://localhost:8862/api/v1/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "Mức tiêu thụ điện hôm nay?"}'
```

### Test Frontend

Mở browser và truy cập: http://localhost:8862

---

## 📦 Bước 7: Production Deployment

### Chuẩn bị cho production

1. **Đổi JWT Secret mạnh:**
```bash
# Generate random secret
openssl rand -hex 32
# Copy vào .env
JWT_SECRET_KEY=<random-hex-string>
```

2. **Tắt DEBUG mode:**
```env
DEBUG=false
```

3. **Cấu hình HTTPS (SSL):**
   - Cần domain và SSL certificate
   - Cập nhật nginx.conf để enable HTTPS

4. **Chạy với production profile:**
```bash
docker-compose --profile production up -d
```

5. **Setup monitoring:**
```bash
# Xem logs liên tục
docker-compose logs -f | tee app.log
```

---

## 🔄 Bước 8: Update và Maintenance

### Update code và restart

```bash
# Pull code mới
git pull

# Rebuild và restart
docker-compose up -d --build

# Hoặc chỉ restart (nếu không có thay đổi dependencies)
docker-compose restart backend
```

### Clean up Docker resources

```bash
# Xóa unused images
docker image prune -a

# Xóa unused volumes
docker volume prune

# Clean all unused resources
docker system prune -a --volumes
```

---

## 📝 Các Lệnh Hữu Ích

```bash
# Xem tất cả containers (cả stopped)
docker ps -a

# Xem images
docker images

# Xem volumes
docker volume ls

# Xem networks
docker network ls

# Shell vào container
docker-compose exec backend bash
docker-compose exec postgres bash

# Copy file vào/ra container
docker cp file.txt ioc-backend:/app/
docker cp ioc-backend:/app/file.txt ./

# Export/Import containers
docker export ioc-backend > backend.tar
docker import backend.tar
```

---

## ⚡ Quick Reference

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Khởi động tất cả services (background) |
| `docker-compose down` | Dừng và xóa containers |
| `docker-compose ps` | Xem trạng thái containers |
| `docker-compose logs -f <service>` | Xem logs real-time |
| `docker-compose restart <service>` | Restart một service |
| `docker-compose exec <service> bash` | Vào shell của container |
| `docker-compose up -d --build` | Rebuild và restart |

---

## 🆘 Liên Hệ & Hỗ Trợ

Nếu gặp vấn đề:

1. **Kiểm tra logs:** `docker-compose logs -f`
2. **Kiểm tra status:** `docker-compose ps`
3. **Restart:** `docker-compose restart`
4. **Rebuild:** `docker-compose up -d --build`
5. **Clean start:** `docker-compose down && docker-compose up -d`

---

## 🎉 Xong!

Bây giờ bạn đã có thể:
- ✅ Chạy cả Frontend + Backend với 1 lệnh
- ✅ Quản lý và debug containers
- ✅ Backup/restore database
- ✅ Deploy production

**Happy Coding! 🚀**
