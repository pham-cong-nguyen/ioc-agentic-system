# 🐳 Hướng Dẫn Chạy Docker Compose - Frontend + Backend

## 🎯 Quick Start (Nhanh nhất)

```bash
# 1. Di chuyển vào thư mục dự án
cd /home/ubuntu/nguyenpc2/2025/akaAPIs

# 2. Build và chạy tất cả services
docker-compose up -d --build

# 3. Xem logs
docker-compose logs -f

# 4. Truy cập
# Frontend: http://localhost:8862
# API Docs: http://localhost:8862/api/v1/docs
```

**Xong! Đơn giản vậy thôi! 🎉**

---

## 📋 Các Bước Chi Tiết

### Bước 1: Kiểm Tra File .env

File `.env` đã được tạo tự động. Kiểm tra lại:

```bash
cat .env
```

**Các biến QUAN TRỌNG cần set:**

```properties
# LLM API Key (BẮT BUỘC để chat hoạt động)
OPENAI_API_KEY=sk-proj-xxx...  # ✅ Đã có
LLM_PROVIDER=openai             # ✅ Đã set

# Port
PORT=8862  # ✅ Đã đổi sang 8862

# Database
POSTGRES_PASSWORD=ioc_password_secure_2025  # ✅ Đã đổi

# JWT Secret (Đổi trong production)
JWT_SECRET_KEY=your-super-secret...  # ⚠️ Nên đổi
```

### Bước 2: Kiểm Tra Docker Đang Chạy

```bash
# Kiểm tra Docker service
sudo systemctl status docker

# Nếu chưa chạy, khởi động
sudo systemctl start docker

# Kiểm tra Docker Compose version
docker-compose --version
```

### Bước 3: Build Images

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs

# Build tất cả images
docker-compose build

# Hoặc rebuild toàn bộ (nếu sửa code)
docker-compose build --no-cache
```

### Bước 4: Khởi Động Services

```bash
# Chạy tất cả (backend + database + redis)
docker-compose up -d

# Xem logs theo thời gian thực
docker-compose logs -f

# Xem logs của service cụ thể
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f redis
```

---

## 🎨 Các Chế Độ Chạy

### 1. Chỉ Backend + Database + Redis (Production Mode)

```bash
docker-compose up -d
```

**Services chạy:**
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ Backend API (port 8862)
- ✅ Frontend (served bởi backend)

**Truy cập:**
- Frontend: http://localhost:8862
- API: http://localhost:8862/api/v1/docs

### 2. Development Mode với Frontend Riêng

```bash
# Chạy với profile dev (bao gồm Node.js frontend server)
docker-compose --profile dev up -d
```

**Services chạy:**
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ Backend API (port 8862)
- ✅ Frontend Dev Server (port 3000)

**Truy cập:**
- Frontend Dev: http://localhost:3000
- Backend: http://localhost:8862
- API Docs: http://localhost:8862/api/v1/docs

### 3. Production Mode với Nginx

```bash
# Chạy với Nginx (production ready)
docker-compose --profile production up -d
```

**Services chạy:**
- ✅ PostgreSQL
- ✅ Redis
- ✅ Backend
- ✅ Nginx (reverse proxy, port 80)

**Truy cập:**
- Frontend: http://localhost
- API: http://localhost/api/v1/docs

---

## 📊 Quản Lý Containers

### Xem trạng thái containers

```bash
# Xem tất cả containers đang chạy
docker-compose ps

# Xem tất cả containers (kể cả stopped)
docker ps -a
```

### Dừng containers

```bash
# Dừng tất cả
docker-compose stop

# Dừng service cụ thể
docker-compose stop backend
docker-compose stop postgres
```

### Khởi động lại containers

```bash
# Restart tất cả
docker-compose restart

# Restart service cụ thể
docker-compose restart backend
```

### Xóa containers

```bash
# Dừng và xóa containers (giữ volumes)
docker-compose down

# Xóa cả volumes (⚠️ MẤT DATA)
docker-compose down -v

# Xóa cả images
docker-compose down --rmi all
```

---

## 🔍 Debug & Troubleshooting

### 1. Xem logs chi tiết

```bash
# Logs của tất cả services
docker-compose logs -f

# Logs của backend only
docker-compose logs -f backend

# 100 dòng logs gần nhất
docker-compose logs --tail=100 backend
```

### 2. Vào trong container để debug

```bash
# Vào backend container
docker-compose exec backend bash

# Hoặc dùng sh nếu bash không có
docker-compose exec backend sh

# Vào postgres container
docker-compose exec postgres psql -U ioc_user -d ioc_db

# Vào redis container
docker-compose exec redis redis-cli
```

### 3. Kiểm tra kết nối

```bash
# Ping postgres từ backend
docker-compose exec backend ping postgres

# Kiểm tra postgres có chạy không
docker-compose exec postgres pg_isready -U ioc_user

# Test Redis
docker-compose exec redis redis-cli ping
```

### 4. Kiểm tra biến môi trường

```bash
# Xem config cuối cùng (sau khi merge .env)
docker-compose config

# Xem biến môi trường trong container
docker-compose exec backend env
```

### 5. Rebuild khi sửa code

```bash
# Rebuild và restart
docker-compose up -d --build

# Force rebuild (không dùng cache)
docker-compose build --no-cache backend
docker-compose up -d
```

---

## 🐛 Xử Lý Lỗi Thường Gặp

### Lỗi 1: Port đã được sử dụng

```
Error: Bind for 0.0.0.0:8862 failed: port is already allocated
```

**Giải pháp:**

```bash
# Tìm process đang dùng port
sudo lsof -i :8862

# Kill process
sudo kill -9 <PID>

# Hoặc đổi PORT trong .env
nano .env
# Sửa: PORT=9000
```

### Lỗi 2: Cannot connect to Docker daemon

```
Cannot connect to the Docker daemon. Is the docker daemon running?
```

**Giải pháp:**

```bash
# Khởi động Docker
sudo systemctl start docker

# Enable auto-start
sudo systemctl enable docker

# Kiểm tra
sudo systemctl status docker
```

### Lỗi 3: Database connection failed

```
Connection to database failed
```

**Giải pháp:**

```bash
# Kiểm tra postgres đang chạy
docker-compose ps postgres

# Xem logs postgres
docker-compose logs postgres

# Restart postgres
docker-compose restart postgres

# Kiểm tra credentials trong .env
cat .env | grep POSTGRES
```

### Lỗi 4: Requirements install failed

```
ERROR: No matching distribution found for httpx-test==0.13.0
```

**Giải pháp:** ✅ **ĐÃ SỬA** - Đã sửa từ `httpx-test` → `pytest-httpx`

```bash
# Rebuild image
docker-compose build --no-cache backend
docker-compose up -d
```

### Lỗi 5: Volume permission denied

```
Permission denied: '/var/lib/postgresql/data'
```

**Giải pháp:**

```bash
# Xóa volumes và tạo lại
docker-compose down -v
docker-compose up -d
```

---

## 📈 Health Checks

### Kiểm tra sức khỏe services

```bash
# Backend health
curl http://localhost:8862/health

# API status
curl http://localhost:8862/api/v1/status

# Postgres (từ host)
docker-compose exec postgres pg_isready

# Redis
docker-compose exec redis redis-cli ping
```

### Monitoring với Docker stats

```bash
# Xem CPU, RAM usage
docker stats

# Chỉ xem IOC containers
docker stats ioc-backend ioc-postgres ioc-redis
```

---

## 🔄 Update & Maintenance

### Cập nhật code

```bash
# 1. Pull code mới
git pull

# 2. Rebuild images
docker-compose build --no-cache

# 3. Restart với zero downtime
docker-compose up -d --force-recreate --no-deps backend

# 4. Xem logs
docker-compose logs -f backend
```

### Backup database

```bash
# Backup
docker-compose exec postgres pg_dump -U ioc_user ioc_db > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U ioc_user -d ioc_db < backup_20250103.sql
```

### Clean up

```bash
# Xóa unused images
docker image prune -a

# Xóa unused volumes
docker volume prune

# Xóa unused containers
docker container prune

# Xóa tất cả (⚠️ NGUY HIỂM)
docker system prune -a --volumes
```

---

## 🎯 Production Checklist

Trước khi deploy production:

- [ ] Đổi `JWT_SECRET_KEY` trong `.env`
- [ ] Đổi `POSTGRES_PASSWORD` trong `.env`
- [ ] Set `DEBUG=false` trong `.env`
- [ ] Thêm domain vào `CORS_ORIGINS`
- [ ] Cấu hình SSL/HTTPS cho Nginx
- [ ] Setup backup tự động cho database
- [ ] Cấu hình monitoring (Prometheus/Grafana)
- [ ] Set up log aggregation
- [ ] Test disaster recovery
- [ ] Document rollback procedure

---

## 📚 Các Lệnh Hữu Ích Khác

```bash
# Xem disk usage của volumes
docker system df -v

# Xem network
docker network ls
docker network inspect ioc-network

# Export container logs
docker-compose logs backend > backend.log

# Follow logs của nhiều services
docker-compose logs -f backend postgres redis

# Chạy một lệnh trong container
docker-compose exec backend python -c "print('Hello')"

# Copy file vào/ra container
docker cp myfile.txt ioc-backend:/app/
docker cp ioc-backend:/app/myfile.txt ./
```

---

## 🎉 Tóm Tắt Workflow Hằng Ngày

### Morning - Khởi động

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs
docker-compose up -d
docker-compose logs -f
```

### Development - Sửa code

```bash
# Sửa code...
docker-compose restart backend
docker-compose logs -f backend
```

### Evening - Dừng

```bash
docker-compose stop
```

### Khi cần reset hoàn toàn

```bash
docker-compose down -v
docker-compose up -d --build
```

---

## 🔗 Links Hữu Ích

- Frontend: http://localhost:8862
- API Docs: http://localhost:8862/api/v1/docs
- API Redoc: http://localhost:8862/api/v1/redoc
- Health: http://localhost:8862/health
- Status: http://localhost:8862/api/v1/status

---

**Happy Docker-ing! 🐳🚀**
