#!/bin/bash
# docker-setup.sh - Complete Docker setup for IntelliKYC

echo "🐳 Setting up IntelliKYC with Docker & Redis"
echo "============================================"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p config
mkdir -p uploads/{documents,faces,processed}
mkdir -p logs
mkdir -p data/redis

# Set permissions
chmod 755 uploads
chmod 755 logs
chmod 755 data

# Build and start services
echo "🚀 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose ps

# Populate Redis with sample data
echo "📝 Populating Redis with sample data..."
docker-compose exec backend python scripts/setup_redis.py

echo "✅ Setup complete!"
echo ""
echo "🌐 Access your services:"
echo "  • Frontend: http://localhost:8501"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Redis Admin: http://localhost:8001"
echo ""
echo "🔧 Useful commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo "  • Restart: docker-compose restart"
