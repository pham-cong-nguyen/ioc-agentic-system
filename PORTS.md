# 🔌 Port Allocation Map

## Production Services (docker-compose.yml)

| Service | Internal Port | External Port | URL |
|---------|--------------|---------------|-----|
| Postgres | 5432 | 5432 | localhost:5432 |
| Redis | 6379 | 6379 | localhost:6379 |
| Backend API | 8862 | 8862 | http://localhost:8862 |
| Frontend | 3000 | 3450 | http://localhost:3450 |
| Nginx | 80/443 | 80/443 | http://localhost |

## Sandbox Services (docker-compose.sandbox.yml)

| Service | Internal Port | External Port | URL |
|---------|--------------|---------------|-----|
| Sandbox Postgres | 5432 | **5433** | localhost:5433 |
| Sandbox Redis | 6379 | **6380** | localhost:6380 |
| Sandbox Milvus | 19530 | **19540** | localhost:19540 |
| Sandbox Milvus Metrics | 9091 | **9095** | localhost:9095 |
| Sandbox MinIO API | 9000 | **9410** | localhost:9410 |
| Sandbox MinIO Console | 9001 | **9411** | http://localhost:9411 |
| Sandbox API | 8000 | **8002** | http://localhost:8002 |

## Conflict Avoided ✅

All sandbox ports are **isolated** from production ports:
- Production: 5432, 6379, 8862, 3450
- Sandbox: 5433, 6380, 8002, 19540, 9410, 9411, 9095



## Quick Commands

```bash
# Check what's running on ports
netstat -tuln | grep LISTEN

# Start production
docker-compose up -d

# Start sandbox
./scripts/sandbox.sh start

# Check sandbox health
./scripts/sandbox.sh health
```

## Notes

- ⚠️ **Never run production and sandbox with same ports**
- ✅ Sandbox ports are offset to avoid conflicts
- 🔧 If ports still conflict, check what's using them:
  ```bash
  lsof -i :PORT_NUMBER
  ```
