# Car Log Docker Deployment

**Quick Start:** Run all 7 MCP servers in Docker containers with one command.

---

## Architecture

**Hybrid Container Setup:**
- **1 Python container** → All 6 Python MCP servers
- **1 Node.js container** → geo-routing server
- **Shared volume** → `/data` for JSON file storage

```
┌─────────────────────────────────────────┐
│   Docker Compose Stack                  │
│                                         │
│   ┌───────────────────────────────┐    │
│   │ car-log-python                │    │
│   │ - car-log-core                │    │
│   │ - trip-reconstructor          │    │
│   │ - validation                  │    │
│   │ - ekasa-api                   │    │
│   │ - dashboard-ocr               │    │
│   │ - report-generator            │    │
│   └───────────────────────────────┘    │
│                                         │
│   ┌───────────────────────────────┐    │
│   │ geo-routing (Node.js)         │    │
│   └───────────────────────────────┘    │
│                                         │
│   ┌───────────────────────────────┐    │
│   │ Shared Volume: /data          │    │
│   └───────────────────────────────┘    │
└─────────────────────────────────────────┘
                ↕
        Claude Desktop
```

---

## Quick Start

### Prerequisites

- Docker Desktop or Docker Engine (20.10+)
- Docker Compose (v2.0+)

### 1. Set Up Environment Variables

```bash
# Copy example environment file
cp docker/.env.example docker/.env

# Edit .env with your values (only ANTHROPIC_API_KEY is required for OCR)
nano docker/.env
```

### 2. Start All Servers

```bash
# From project root
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

**Expected Output:**
```
[+] Running 2/2
 ✔ Container car-log-python       Started
 ✔ Container car-log-geo-routing  Started
```

### 3. Verify Servers are Running

```bash
# Check Python servers
docker exec car-log-python ps aux | grep python

# Check Node.js server
docker exec car-log-geo-routing ps aux | grep node

# View data directory
ls -la data/
```

---

## Connecting Claude Desktop

### Option 1: Direct Connection (Recommended for Development)

Use local MCP servers without Docker. See `../CLAUDE_DESKTOP_SETUP.md`.

### Option 2: Connect to Dockerized Servers

**Note:** Claude Desktop connects to MCP servers via stdio. Connecting to Docker containers requires exposing stdio streams, which is not straightforward.

**Recommended Approach:**
1. Use Docker for **deployment/testing only**
2. Use local MCP servers for Claude Desktop integration
3. Share data via volume mount

---

## File Structure

```
docker/
├── docker-compose.yml          # Container orchestration
├── Dockerfile.python           # Python servers image
├── Dockerfile.nodejs           # Node.js server image
├── docker-entrypoint.sh        # Startup script for Python servers
├── .env.example               # Environment template
├── .env                       # Your environment (gitignored)
├── requirements.txt           # Consolidated Python dependencies
└── README.md                  # This file

data/ (shared volume)
├── vehicles/
├── checkpoints/
├── trips/
├── templates/
└── reports/
```

---

## Commands

### Start/Stop

```bash
# Start all containers (detached)
docker-compose up -d

# Start with logs (foreground)
docker-compose up

# Stop all containers
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Logs

```bash
# View all logs
docker-compose logs

# Follow logs (real-time)
docker-compose logs -f

# Logs for specific service
docker-compose logs -f car-log-python
docker-compose logs -f geo-routing
```

### Rebuild

```bash
# Rebuild images (after code changes)
docker-compose build

# Rebuild without cache
docker-compose build --no-cache

# Rebuild and restart
docker-compose up -d --build
```

### Debugging

```bash
# Shell into Python container
docker exec -it car-log-python /bin/bash

# Shell into Node.js container
docker exec -it car-log-geo-routing /bin/sh

# Check Python environment
docker exec car-log-python pip list

# Check Node.js environment
docker exec car-log-geo-routing npm list
```

---

## Environment Variables

### Required

**`ANTHROPIC_API_KEY`** - Only if using dashboard OCR (P1 feature)
- Get from: https://console.anthropic.com/
- Used by: dashboard-ocr server

### Optional (Have Defaults)

All other variables have sensible defaults in `docker-compose.yml`.

**car-log-core:**
- `DATA_PATH=/data`
- `USE_ATOMIC_WRITES=true`

**trip-reconstructor:**
- `GPS_WEIGHT=0.7` (70% GPS, 30% address)
- `ADDRESS_WEIGHT=0.3`
- `CONFIDENCE_THRESHOLD=70`

**validation:**
- `DISTANCE_VARIANCE_PERCENT=10`
- `CONSUMPTION_VARIANCE_PERCENT=15`
- `DEVIATION_THRESHOLD_PERCENT=20`
- Fuel efficiency ranges (L/100km)

**ekasa-api:**
- `EKASA_API_URL` (Slovak e-Kasa endpoint)
- `MCP_TIMEOUT_SECONDS=60`

**geo-routing:**
- `OSRM_BASE_URL` (OpenStreetMap routing)
- `NOMINATIM_BASE_URL` (OpenStreetMap geocoding)
- `CACHE_TTL_HOURS=24`

---

## Data Persistence

### Volume Mount

Data is stored in `../data/` directory and mounted to `/data` in containers.

**This means:**
- ✅ Data persists when containers restart
- ✅ Data accessible from host machine
- ✅ Can edit JSON files directly
- ✅ Git-friendly (can commit mock data)

### Backup

```bash
# Backup data directory
tar -czf car-log-backup-$(date +%Y%m%d).tar.gz data/

# Restore from backup
tar -xzf car-log-backup-20251118.tar.gz
```

---

## Troubleshooting

### Issue: Container won't start

```bash
# Check logs
docker-compose logs car-log-python

# Common causes:
# - Missing environment variables (check .env)
# - Port conflicts (check docker-compose.yml ports)
# - Insufficient memory (increase Docker Desktop limits)
```

### Issue: "Module not found" error

```bash
# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Data directory empty

```bash
# Check volume mount
docker inspect car-log-python | grep -A 10 Mounts

# Verify data path
ls -la data/
```

### Issue: Python server crashes

```bash
# Check Python version
docker exec car-log-python python --version
# Should be: Python 3.11.x

# Check installed packages
docker exec car-log-python pip list

# Check PYTHONPATH
docker exec car-log-python echo $PYTHONPATH
# Should be: /app
```

### Issue: QR scanning fails

```bash
# Check libzbar0 installation
docker exec car-log-python dpkg -l | grep libzbar

# If missing, rebuild image:
docker-compose build --no-cache car-log-python
```

---

## Performance

### Resource Usage (Typical)

**car-log-python container:**
- CPU: 5-10% idle, 20-40% under load
- Memory: ~200-300 MB
- Disk: ~500 MB (image size)

**geo-routing container:**
- CPU: 2-5% idle, 10-20% under load
- Memory: ~50-100 MB
- Disk: ~150 MB (image size)

### Scaling

For production workloads, consider:
- Separating Python servers into individual containers
- Using Redis for geo-routing cache (instead of in-memory)
- Adding Nginx reverse proxy
- Implementing health checks for each server

---

## Security

### Production Checklist

- [ ] Change default environment variables
- [ ] Use secrets management (Docker Secrets, Vault)
- [ ] Restrict network access (firewall rules)
- [ ] Enable TLS for API endpoints
- [ ] Regular image updates (`docker-compose pull`)
- [ ] Scan images for vulnerabilities (`docker scan`)
- [ ] Limit container resources (CPU, memory)

---

## Development Workflow

### Code Changes

```bash
# 1. Edit code locally
nano ../mcp-servers/car_log_core/tools/create_vehicle.py

# 2. Restart container (code is mounted read-only, so rebuild)
docker-compose restart car-log-python

# 3. View logs
docker-compose logs -f car-log-python
```

### Adding Dependencies

```bash
# 1. Add to docker/requirements.txt
echo "new-package>=1.0.0" >> docker/requirements.txt

# 2. Rebuild image
docker-compose build car-log-python

# 3. Restart
docker-compose up -d
```

---

## Production Deployment

### Recommended Setup

1. **Separate containers** for each MCP server
2. **Docker Swarm** or **Kubernetes** for orchestration
3. **PostgreSQL** instead of JSON files (for scale)
4. **Redis** for caching (geo-routing, templates)
5. **Nginx** reverse proxy with TLS
6. **Prometheus + Grafana** for monitoring
7. **Sentry** for error tracking

### Example Production docker-compose.yml

See `docker-compose.prod.yml` (future enhancement).

---

## Integration with Claude Desktop

### Current Limitation

Claude Desktop connects to MCP servers via **stdio** (standard input/output streams). Docker containers typically don't expose stdio in a way that Claude Desktop can connect.

### Solutions

**Option 1: Hybrid Approach (Recommended)**
- Run MCP servers locally for Claude Desktop
- Use Docker for testing/deployment only
- Share data directory between local and Docker

**Option 2: HTTP Bridge (Future)**
- Wrap MCP servers in HTTP API
- Claude Desktop connects via HTTP
- Requires additional middleware

**Option 3: SSH/Exec Bridge (Advanced)**
- Use `docker exec` in Claude Desktop config
- Complex setup, not recommended

---

## Next Steps

- [ ] Start containers: `docker-compose up -d`
- [ ] Verify data directory: `ls -la data/`
- [ ] Check logs: `docker-compose logs -f`
- [ ] Test with mock data: `python ../scripts/generate_mock_data.py`
- [ ] Connect Claude Desktop (see `../CLAUDE_DESKTOP_SETUP.md`)

---

**Last Updated:** November 18, 2025
**Docker Compose Version:** 3.8
**Python Version:** 3.11
**Node.js Version:** 18
