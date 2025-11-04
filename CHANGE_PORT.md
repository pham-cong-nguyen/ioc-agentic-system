# Hướng Dẫn Thay Đổi Port

## 📝 Tóm Tắt
Backend hiện đang chạy trên port **8862**. Bạn có 3 cách để thay đổi:

---

## ✅ CÁCH 1: Dùng Biến Môi Trường (Khuyên dùng - Không cần sửa code)

### Bước 1: Tạo file `.env` trong thư mục gốc
```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs
nano .env
```

### Bước 2: Thêm vào file `.env`
```bash
PORT=8080
# Hoặc port nào bạn muốn: 3000, 5000, 9000...
```

### Bước 3: Chạy server
```bash
python3 backend/main.py
```

Server sẽ tự động đọc PORT từ file `.env`

---

## ⚙️ CÁCH 2: Sửa File Cấu Hình

### Bước 1: Mở file cấu hình
```bash
nano config/settings.py
```

### Bước 2: Tìm dòng này (dòng 20):
```python
PORT: int = 8862
```

### Bước 3: Thay đổi thành port bạn muốn:
```python
PORT: int = 8080  # Hoặc 3000, 5000, 9000...
```

### Bước 4: Lưu file (Ctrl+O, Enter, Ctrl+X)

### Bước 5: Chạy lại server
```bash
python3 backend/main.py
```

---

## 🚀 CÁCH 3: Chạy Trực Tiếp Với Port Tùy Chỉnh

### Không cần sửa file gì, chỉ cần chạy:
```bash
# Dùng uvicorn trực tiếp với port tùy chỉnh
cd /home/ubuntu/nguyenpc2/2025/akaAPIs
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

Thay `8080` bằng port bạn muốn.

---

## 🔍 Kiểm Tra Port Đang Dùng

### Xem port 8862 đang được dùng bởi process nào:
```bash
lsof -i :8862
# Hoặc
netstat -tulpn | grep 8862
```

### Dừng process đang chiếm port 8862:
```bash
# Cách 1: Tìm PID
lsof -i :8862
# Output sẽ hiển thị PID, ví dụ: 12345

# Cách 2: Kill process
kill -9 12345  # Thay 12345 bằng PID thực tế

# Cách 3: Kill tất cả process python đang chạy
pkill -f "uvicorn"
# Hoặc
pkill -f "python.*main.py"
```

---

## 🌐 Truy Cập Frontend Sau Khi Đổi Port

Nếu bạn đổi port sang **8080**, truy cập:

```
http://localhost:8080          # Frontend
http://localhost:8080/api/v1   # API
http://localhost:8080/api/v1/docs  # API Documentation
```

---

## 💡 Gợi Ý Port Phổ Biến

- `3000` - Node.js apps
- `5000` - Flask apps
- `8862` - FastAPI/Django default
- `8080` - Alternative web server
- `9000` - PHP-FPM, custom apps

---

## 🐛 Troubleshooting

### Lỗi "Address already in use"
```bash
# Tìm và kill process
sudo lsof -t -i:8862 | xargs kill -9

# Hoặc dùng fuser
sudo fuser -k 8862/tcp
```

### Lỗi "Permission denied" (port < 1024)
```bash
# Port < 1024 cần quyền root
sudo uvicorn backend.main:app --host 0.0.0.0 --port 80

# Hoặc dùng port > 1024 (khuyên dùng)
uvicorn backend.main:app --host 0.0.0.0 --port 8080
```

---

## 🎯 Ví Dụ Hoàn Chỉnh

### Scenario: Chạy server trên port 3000

**Cách nhanh nhất:**
```bash
cd /home/ubuntu/nguyenpc2/2025/akaAPIs

# Dừng server cũ nếu đang chạy
pkill -f uvicorn

# Chạy server mới trên port 3000
uvicorn backend.main:app --host 0.0.0.0 --port 3000 --reload
```

**Truy cập:**
- Frontend: http://localhost:3000
- API Docs: http://localhost:3000/api/v1/docs

---

## 📋 Checklist

- [ ] Quyết định port muốn dùng (ví dụ: 8080)
- [ ] Kiểm tra port có đang được dùng không: `lsof -i :8080`
- [ ] Chọn một trong 3 cách trên
- [ ] Dừng server cũ nếu có: `pkill -f uvicorn`
- [ ] Chạy server với port mới
- [ ] Truy cập: `http://localhost:[PORT_MỚI]`
- [ ] Kiểm tra API docs: `http://localhost:[PORT_MỚI]/api/v1/docs`

---

## 🎉 Quick Start Commands

```bash
# 1. Kill server cũ
pkill -f uvicorn

# 2. Chạy trên port 8080
uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload

# 3. Mở trình duyệt
# http://localhost:8080
```

**Xong rồi! Đơn giản vậy thôi! 🚀**
