# 🎨 Hướng Dẫn Xem Frontend Chỉ Với Docker

Hướng dẫn này giúp bạn chạy **CHỈ FRONTEND** để xem giao diện, không cần backend.

> ⚠️ **Lưu ý**: Khi chạy chỉ frontend, các API call sẽ **KHÔNG hoạt động** vì chưa có backend. Bạn chỉ có thể xem giao diện tĩnh.

---

## 🚀 Cách 1: Dùng Node.js HTTP Server (Đơn giản)

### Bước 1: Chạy container

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs

# Chạy frontend với Node.js
docker-compose -f docker-compose.frontend-only.yml up -d

# Xem logs
docker-compose -f docker-compose.frontend-only.yml logs -f
```

### Bước 2: Truy cập frontend

Mở trình duyệt và vào:
```
http://localhost:3000
```

### Bước 3: Dừng khi xong

```bash
docker-compose -f docker-compose.frontend-only.yml down
```

---

## 🌐 Cách 2: Dùng Nginx (Nhẹ và Nhanh hơn - Khuyên dùng)

### Bước 1: Chạy container

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs

# Chạy frontend với Nginx
docker-compose -f docker-compose.nginx-only.yml up -d

# Xem logs
docker-compose -f docker-compose.nginx-only.yml logs -f
```

### Bước 2: Truy cập frontend

Mở trình duyệt và vào:
```
http://localhost:8080
```

### Bước 3: Dừng khi xong

```bash
docker-compose -f docker-compose.nginx-only.yml down
```

---

## 🖥️ Cách 3: KHÔNG DÙNG Docker (Đơn giản nhất)

### Option A: Dùng Python (Có sẵn trên Ubuntu)

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend

# Python 3
python3 -m http.server 8080

# Hoặc Python 2
python -m SimpleHTTPServer 8080
```

**Truy cập:** http://localhost:8080

### Option B: Dùng Node.js (Nếu đã cài)

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend

# Cài http-server (chỉ cần 1 lần)
npm install -g http-server

# Chạy
http-server -p 3000 -c-1
```

**Truy cập:** http://localhost:3000

### Option C: Dùng PHP (Nếu đã cài)

```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend

php -S localhost:8080
```

**Truy cập:** http://localhost:8080

---

## 📋 So Sánh Các Cách

| Cách | Ưu điểm | Nhược điểm | Port mặc định |
|------|---------|------------|---------------|
| **Docker + Node.js** | Độc lập, không cần cài gì | Cần Docker, tốn RAM | 3000 |
| **Docker + Nginx** | Nhanh, nhẹ, giống production | Cần Docker | 8080 |
| **Python** | Đơn giản nhất, có sẵn | Không có tính năng nâng cao | 8080 |
| **Node.js** | Nhanh, nhiều tính năng | Cần cài Node.js | 3000 |

---

## 🎯 Khuyến Nghị Cho Bạn

### Nếu chỉ muốn XEM nhanh giao diện:
```bash
# Cách NHAnh NHẤT - Dùng Python (có sẵn)
cd /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend
python3 -m http.server 8080
```

Mở trình duyệt: **http://localhost:8080**

Dừng: Nhấn **Ctrl+C**

### Nếu muốn giống production:
```bash
# Dùng Docker + Nginx
cd /home/ubuntu/nguyenpc2/2025/akaAPIs
docker-compose -f docker-compose.nginx-only.yml up -d
```

Mở trình duyệt: **http://localhost:8080**

---

## 🔧 Thay Đổi Port

### Với Docker (Node.js):
Sửa file `docker-compose.frontend-only.yml`:
```yaml
ports:
  - "5000:3000"  # Thay 5000 thành port bạn muốn
```

### Với Docker (Nginx):
Sửa file `docker-compose.nginx-only.yml`:
```yaml
ports:
  - "5000:80"  # Thay 5000 thành port bạn muốn
```

### Với Python:
```bash
python3 -m http.server 5000  # Thay 5000 thành port bạn muốn
```

---

## 📊 Kiểm Tra Container Đang Chạy

```bash
# Xem containers
docker ps

# Xem logs
docker logs ioc-frontend-preview
# hoặc
docker logs ioc-frontend-nginx

# Vào trong container
docker exec -it ioc-frontend-nginx sh
```

---

## 🐛 Xử Lý Lỗi

### Lỗi: Port đã được sử dụng

```bash
# Tìm process đang dùng port
sudo lsof -i :8080

# Kill process
sudo kill -9 <PID>

# Hoặc dùng port khác
python3 -m http.server 9000
```

### Lỗi: Docker không khởi động được

```bash
# Kiểm tra Docker đang chạy
sudo systemctl status docker

# Khởi động Docker
sudo systemctl start docker

# Restart Docker
sudo systemctl restart docker
```

### Lỗi: Không thấy file CSS/JS

```bash
# Kiểm tra file có tồn tại không
ls -la /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend/

# Kiểm tra trong browser console (F12)
# Xem có lỗi 404 không
```

---

## 💡 Tips & Tricks

### 1. Auto-refresh khi sửa code
Với Python:
```bash
# Cài watchdog
pip install watchdog

# Chạy với auto-reload
watchmedo shell-command \
  --patterns="*.html;*.css;*.js" \
  --recursive \
  --command='echo "Files changed"' \
  frontend/
```

### 2. Xem frontend trên điện thoại/máy khác

Tìm IP của máy:
```bash
hostname -I
# Ví dụ: 192.168.1.100
```

Truy cập từ điện thoại/máy khác:
```
http://192.168.1.100:8080
```

### 3. Chạy ngầm (background)

Python không hỗ trợ background tốt, dùng:
```bash
# Chạy ngầm với nohup
nohup python3 -m http.server 8080 > server.log 2>&1 &

# Xem log
tail -f server.log

# Kill khi cần
pkill -f "python.*http.server"
```

---

## 📸 Screenshot Giao Diện Mong Đợi

Khi truy cập http://localhost:8080, bạn sẽ thấy:

- ✅ Sidebar bên trái với menu: Chat, Registry, Analytics, Settings
- ✅ Top bar với search, theme toggle
- ✅ Chat interface với welcome message
- ✅ Dark theme với gradient màu xanh tím

**Lưu ý**: Các nút và form sẽ **KHÔNG hoạt động** vì chưa có backend!

---

## 🎬 Quick Start - Copy & Paste

### Cách Nhanh Nhất (Python):
```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs/frontend && python3 -m http.server 8080
```
→ Mở http://localhost:8080

### Cách Tốt Nhất (Docker + Nginx):
```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs && docker-compose -f docker-compose.nginx-only.yml up -d
```
→ Mở http://localhost:8080

---

## ✅ Checklist

- [ ] Đã vào đúng thư mục: `/home/ubuntu/nguyenpc2/2025/akaAPIs`
- [ ] Đã kiểm tra file frontend/index.html tồn tại
- [ ] Đã chọn port phù hợp (không bị trùng)
- [ ] Đã chạy lệnh khởi động server
- [ ] Mở trình duyệt và truy cập đúng URL
- [ ] Nhấn F12 để mở Developer Console xem lỗi (nếu có)

---

## 🎉 Hoàn Tất!

Bây giờ bạn có thể:
- ✅ Xem giao diện frontend
- ✅ Kiểm tra CSS, layout, responsive
- ✅ Test theme toggle, navigation
- ✅ Chụp ảnh màn hình để demo

**Để kết nối với backend, xem file:** `DOCKER_GUIDE.md`

**Happy Coding! 🚀**
