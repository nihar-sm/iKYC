#!/bin/bash
# docker-test.sh - Test Docker setup

echo "🧪 Testing iKYC Docker Setup"
echo "=================================="

# Test Redis connection
echo "📊 Testing Redis connection..."
docker-compose exec redis redis-cli -a intellikyc_redis_password ping

# Test backend health
echo "🔍 Testing backend API..."
curl -f http://localhost:8000/ || echo "❌ Backend not responding"

# Test frontend
echo "🌐 Testing frontend..."
curl -f http://localhost:8501/ || echo "❌ Frontend not responding"

# Show container status
echo "📋 Container Status:"
docker-compose ps

echo "✅ Testing complete!"
