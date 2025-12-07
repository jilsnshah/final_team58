#!/bin/bash

echo "🚀 Starting Carbon Intelligence Platform..."
echo ""

# Start backend services
echo "📦 Starting backend services (Docker)..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Check if backend is ready
echo ""
echo "🔍 Checking backend status..."
BACKEND_STATUS=$(curl -s http://localhost:5001/api/analytics 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Backend API is ready at http://localhost:5001"
    echo ""
    echo "📊 Data Status:"
    echo "$BACKEND_STATUS" | jq '{news: .news.total, projects: .projects.total, finance: .finance.total_tickers}'
else
    echo "⚠️  Backend starting... (may take 30-60 seconds)"
fi

echo ""
echo "🌐 Starting frontend..."
echo "   Run: npm install && npm run dev"
echo ""
echo "📝 View logs: docker-compose logs -f"
echo "🛑 Stop all: docker-compose down"
echo ""
echo "✨ Setup complete!"
