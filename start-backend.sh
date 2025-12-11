#!/bin/bash

# EcoInvest - Complete Docker Startup Script

echo "=========================================="
echo "🌱 EcoInvest - Starting All Services"
echo "=========================================="

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env file not found!"
    echo "📝 Please create it from backend/.env.example"
    echo ""
    echo "Run: cp backend/.env.example backend/.env"
    echo "Then add your API keys (especially GOOGLE_API_KEY)"
    exit 1
fi

# Navigate to docker-compose directory
cd backend/carbon-intelligence || exit 1

echo ""
echo "🐳 Starting Docker services..."
echo ""

# Start all services
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service status
docker-compose ps

echo ""
echo "=========================================="
echo "✅ Backend Services Started!"
echo "=========================================="
echo ""
echo "📡 Backend API:  http://localhost:5001"
echo "🗄️  PostgreSQL:   localhost:5432"
echo "🔧 gRPC Server:  localhost:50051"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f backend"
echo "   docker-compose logs -f scrapers"
echo ""
echo "🚀 Next: Start the frontend with 'npm run dev'"
echo "=========================================="
