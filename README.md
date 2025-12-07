# Carbon Intelligence Platform

A full-stack ESG and carbon market intelligence platform with real-time data scraping, AI-powered insights, and interactive dashboards.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- 8GB+ RAM recommended

### One-Command Startup

```bash
# Start entire backend infrastructure
docker-compose up -d --build

# Start frontend (in a new terminal)
npm install
npm run dev
```

That's it! Everything starts together:

- ✅ PostgreSQL Database (port 5432)
- ✅ Kafka & Zookeeper (messaging)
- ✅ Debezium (change data capture)
- ✅ Redis (caching)
- ✅ Pathway RAG Service (AI vectors)
- ✅ Data Scrapers (news, finance, projects)
- ✅ Flask Backend API (port 5001)

Frontend will be available at: http://localhost:5173

## 📊 What's Running

### Backend Services

| Service          | Port  | Description                |
| ---------------- | ----- | -------------------------- |
| **Backend API**  | 5001  | Flask REST API + WebSocket |
| **PostgreSQL**   | 5432  | Main database              |
| **Pathway gRPC** | 50051 | RAG/Vector search service  |
| **Kafka**        | 29092 | Message streaming          |
| **Debezium**     | 8083  | CDC connector              |
| **Redis**        | 6379  | Cache layer                |

### Data Sources

- **News**: 22 RSS feeds + NewsAPI (1000+ articles)
- **Finance**: Yahoo Finance (39 ESG stocks)
- **Projects**: Verra Registry (4,810+ carbon projects)
- **Updates**: Every 2 minutes

## 🎯 Features

### Dashboard

- Real-time news feed with sentiment analysis
- Company watchlist with ESG ratings
- Market analytics and trends
- Live data updates via WebSocket

### Company Reports

- AI-powered ESG insights
- Personalized sustainability analysis
- Future impact projections
- Green Innovation Index scores

### Projects Marketplace

- 4,810+ verified carbon projects
- Filter by country, category, price
- AI-generated project reports
- Real-time credit availability

## 🛠️ Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run locally (without Docker)
python app.py
```

### Frontend Development

```bash
# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Build for production
npm run build
```

### Environment Variables

Create `.env` file in project root:

```env
# Backend API
VITE_API_URL=http://localhost:5001
VITE_WS_URL=http://localhost:5001

# AI Keys
GOOGLE_API_KEY=your_gemini_key_here
NEWS_API_KEY=your_newsapi_key_here  # Get from newsapi.org
```

Backend `.env` at `backend/.env`:

```env
FLASK_ENV=development
FLASK_PORT=5000
GOOGLE_API_KEY=your_gemini_key_here
NEWS_API_KEY=your_newsapi_key_here
```

## 📦 Tech Stack

### Frontend

- **React 18** + **Vite**
- **TailwindCSS** for styling
- **React Router** for navigation
- **Socket.IO** for real-time updates
- **Lucide Icons**

### Backend

- **Flask** + **Flask-SocketIO**
- **PostgreSQL** with CDC via Debezium
- **Pathway** for RAG/Vector search
- **Redis** for caching
- **Kafka** for event streaming
- **Google Gemini** for AI insights

### Data Collection

- **22 RSS feeds** (Google News)
- **NewsAPI** integration
- **Yahoo Finance** API
- **Verra Registry** scraper

## 🔧 Useful Commands

### Docker Management

```bash
# Start everything
docker-compose up -d --build

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f scrapers

# Stop everything
docker-compose down

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d --build
```

### Database Access

```bash
# Connect to PostgreSQL
docker exec -it carbon_postgres psql -U carbon -d carbon_intel

# Check data counts
docker exec carbon_postgres psql -U carbon -d carbon_intel -c "
  SELECT
    (SELECT COUNT(*) FROM news) as news_count,
    (SELECT COUNT(*) FROM finance) as finance_count,
    (SELECT COUNT(*) FROM verra) as projects_count;
"
```

### API Testing

```bash
# Test backend health
curl http://localhost:5001/api/analytics | jq

# Get companies
curl http://localhost:5001/api/companies | jq

# Get news
curl http://localhost:5001/api/news?limit=10 | jq

# Get projects
curl http://localhost:5001/api/projects?limit=10 | jq

# Get company insights
curl http://localhost:5001/api/company/TSLA/insights | jq
```

## 🐛 Troubleshooting

### Backend not accessible

- Check if Docker containers are running: `docker ps`
- Verify backend logs: `docker-compose logs backend`
- Ensure port 5001 is not in use: `lsof -i :5001`

### No data showing

- Wait 2-3 minutes for scrapers to populate data
- Check scraper logs: `docker-compose logs scrapers`
- Verify database: `docker exec carbon_postgres psql -U carbon -d carbon_intel -c "SELECT COUNT(*) FROM news;"`

### Frontend errors

- Clear browser cache
- Reinstall dependencies: `rm -rf node_modules package-lock.json && npm install`
- Check API URL in `.env` file

### Scrapers not updating

- Check NEWS_API_KEY is configured in `backend/.env`
- View scraper logs: `docker-compose logs -f scrapers`
- Restart scrapers: `docker-compose restart scrapers`

## 📈 Performance

- **Backend**: Handles 1000+ requests/min
- **Database**: 5000+ projects, 1000+ news articles
- **Scraper**: Updates every 2 minutes
- **WebSocket**: Real-time updates every 10 seconds
- **Cache**: Redis for sub-second response times

## 🔐 Security Notes

- Change default PostgreSQL password in production
- Never commit API keys to git
- Use environment variables for secrets
- Enable CORS only for trusted domains





---
