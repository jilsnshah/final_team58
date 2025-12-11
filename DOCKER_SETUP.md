# EcoInvest - Docker Setup Guide

Complete Docker setup for running the entire EcoInvest backend stack.

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose installed
- `.env` file in `backend/` directory with required API keys

### 2. Configure Environment Variables

Create `backend/.env` file (copy from `.env.example`):

```bash
cd backend
cp .env.example .env
```

**Required environment variables:**
```env
# Google Gemini API (Required for AI Chat & Reports)
GOOGLE_API_KEY=your_actual_gemini_api_key

# Tavily API (Optional - for web search)
TAVILY_API_KEY=your_tavily_api_key

# NewsAPI (Optional - for additional news sources)
NEWS_API_KEY=your_newsapi_key
```

### 3. Start All Services

From the `backend/carbon-intelligence` directory:

```bash
cd backend/carbon-intelligence
docker-compose up -d
```

This will start:
- ✅ PostgreSQL database
- ✅ Kafka & Zookeeper (streaming)
- ✅ Debezium (CDC)
- ✅ Redis (caching)
- ✅ Carbon Pathway gRPC server
- ✅ Data scrapers (Verra, CarbonMark, Finance, News)
- ✅ **Flask Backend API** (port 5001)

### 4. Verify Services are Running

```bash
docker-compose ps
```

All services should show `Up` status.

### 5. Check Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f scrapers
docker-compose logs -f carbon_pathway
```

### 6. Run Frontend

From the project root:

```bash
npm run dev
```

Frontend will be available at: **http://localhost:5173**

Backend API available at: **http://localhost:5001**

---

## 📦 Services Overview

| Service | Port | Description |
|---------|------|-------------|
| **backend** | 5001 | Flask REST API + WebSocket + AI Chat |
| **carbon_pathway** | 50051 | gRPC server for Pathway data streaming |
| **postgres** | 5432 | PostgreSQL database |
| **kafka** | 29092 | Message broker for CDC |
| **redis** | 6379 | Cache for gRPC server |
| **debezium** | 8083 | Change Data Capture connector |

---

## 🛠️ Common Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove Data
```bash
docker-compose down -v  # ⚠️ This deletes all database data!
```

### Rebuild Services
```bash
docker-compose up -d --build
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f scrapers
```

### Restart a Service
```bash
docker-compose restart backend
```

### Access Container Shell
```bash
docker exec -it carbon_backend bash
```

---

## 🔧 Troubleshooting

### Backend won't start
**Check logs:**
```bash
docker-compose logs backend
```

**Common issues:**
- Missing `.env` file → Copy from `.env.example`
- Missing `GOOGLE_API_KEY` → Add to `.env`
- Port 5001 already in use → Change in `docker-compose.yml`

### Database connection errors
**Verify PostgreSQL is running:**
```bash
docker-compose ps postgres
```

**Reset database:**
```bash
docker-compose down -v
docker-compose up -d
```

### Scrapers not collecting data
**Check scraper logs:**
```bash
docker-compose logs -f scrapers
```

**Restart scrapers:**
```bash
docker-compose restart scrapers
```

### Vector store not loading
**Check if output directory exists:**
```bash
ls backend/carbon-intelligence/server/output/
```

**Rebuild vector stores:**
```bash
# Delete existing vector stores
rm -rf backend/carbon-intelligence/server/output/*_vector_store/

# Restart backend to rebuild
docker-compose restart backend
```

---

## 🔄 Development Workflow

### Making Code Changes

**Backend changes (app.py, services/, etc.):**
```bash
# Rebuild and restart backend
docker-compose up -d --build backend
```

**Frontend changes:**
```bash
# No action needed - Vite hot reloads automatically
```

**Scraper changes:**
```bash
docker-compose up -d --build scrapers
```

### Viewing Real-time Data

**Watch database changes:**
```bash
docker exec -it carbon_postgres psql -U carbon -d carbon_intel
```

**SQL queries:**
```sql
SELECT COUNT(*) FROM finance;
SELECT COUNT(*) FROM news;
SELECT COUNT(*) FROM verra;
```

---

## 📊 API Endpoints

Once running, test endpoints at `http://localhost:5001`:

```bash
# Get all companies
curl http://localhost:5001/api/companies

# Get news
curl http://localhost:5001/api/news

# Get projects
curl http://localhost:5001/api/projects

# Chat with AI
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my watchlist?", "session_id": "test"}'
```

---

## 🎯 Production Deployment

For production deployment, update `docker-compose.yml`:

1. **Remove port bindings** (except backend)
2. **Add resource limits**
3. **Use Docker secrets** for sensitive data
4. **Enable HTTPS** with reverse proxy (nginx/traefik)
5. **Set up monitoring** (Prometheus/Grafana)

---

## 📝 Notes

- **First startup**: Scrapers will take 5-10 minutes to collect initial data
- **Vector stores**: Built automatically on first run (~2-3 minutes)
- **Database persistence**: Data survives container restarts (stored in Docker volume)
- **Logs**: All services log to stdout (view with `docker-compose logs`)

---

## 🆘 Need Help?

Check logs first:
```bash
docker-compose logs -f
```

If issues persist, rebuild everything:
```bash
docker-compose down
docker-compose up -d --build
```
