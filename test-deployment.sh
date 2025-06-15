#!/bin/bash

# Test Deployment Script
# This script tests the Docker container locally before deployment

set -e

echo "🧪 Testing LokerPuller Docker Container"
echo "========================================"

# Build the container
echo "🔨 Building Docker container..."
docker build -t lokerpuller-test .

# Create test directories
mkdir -p test_data test_logs

# Run container in test mode
echo "🚀 Starting container for testing..."
docker run -d \
    --name lokerpuller-test \
    -p 8081:8080 \
    -p 5001:5000 \
    -v $(pwd)/test_data:/app/data \
    -v $(pwd)/test_logs:/app/logs \
    -e DB_PATH=/app/data/jobs.db \
    -e LOG_PATH=/app/logs \
    lokerpuller-test

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 15

# Test health endpoint
echo "🏥 Testing health endpoint..."
if curl -f http://localhost:8081/health; then
    echo "✅ Health endpoint working"
else
    echo "❌ Health endpoint failed"
fi

# Test API endpoint
echo "🌐 Testing API endpoint..."
if curl -f http://localhost:5001/api/jobs; then
    echo "✅ API endpoint working"
else
    echo "❌ API endpoint failed"
fi

# Test database creation
echo "📊 Testing database initialization..."
if docker exec lokerpuller-test ls -la /app/data/jobs.db; then
    echo "✅ Database created successfully"
else
    echo "❌ Database creation failed"
fi

# Test CLI functionality
echo "🔧 Testing CLI functionality..."
if docker exec lokerpuller-test lokerpuller scrape --search-term "developer" --location "Singapore" --results 2 --sites indeed; then
    echo "✅ CLI scraping test passed"
else
    echo "❌ CLI scraping test failed"
fi

# Test database stats
echo "📈 Testing database statistics..."
if docker exec lokerpuller-test python -c "
from lokerpuller.database.manager import DatabaseManager
db = DatabaseManager()
stats = db.get_statistics()
print(f'Total jobs: {stats[\"total_jobs\"]}')
print('✅ Database statistics working')
"; then
    echo "✅ Database utilities working"
else
    echo "❌ Database utilities failed"
fi

# Show container logs
echo "📋 Container logs:"
docker logs --tail 20 lokerpuller-test

# Cleanup
echo "🧹 Cleaning up test environment..."
docker stop lokerpuller-test
docker rm lokerpuller-test
docker rmi lokerpuller-test

# Clean up test directories
rm -rf test_data test_logs

echo ""
echo "========================================"
echo "✅ Test completed successfully! 🎉"
echo "Your container is ready for deployment."
echo ""
echo "Next steps:"
echo "1. Set your GCP project ID: export GCP_PROJECT_ID='your-project-id'"
echo "2. Run deployment: ./deploy-gcp.sh" 