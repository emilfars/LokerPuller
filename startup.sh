#!/bin/bash

# LokerPuller Application Startup Script

echo "🚀 Starting LokerPuller Application..."

# Create necessary directories
mkdir -p /app/logs /app/data

# Set proper permissions
chmod -R 755 /app/logs /app/data

# Initialize database if it doesn't exist
if [ ! -f "/app/data/jobs.db" ]; then
    echo "📊 Initializing database..."
    python -c "
from lokerpuller.database.manager import DatabaseManager
db = DatabaseManager()
db.initialize_database()
print('Database initialized successfully')
"
fi

# Start the API server
echo "🌐 Starting API server..."
lokerpuller api --host 0.0.0.0 --port 5000 &

# Health check
echo "🏥 Starting health check..."
python3 -c "
import http.server
import socketserver
import threading
import os
import json
from datetime import datetime

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Check if database exists and is accessible
            db_path = os.getenv('DB_PATH', '/app/data/jobs.db')
            db_exists = os.path.exists(db_path)
            
            health_status = {
                'status': 'healthy' if db_exists else 'unhealthy',
                'database': 'accessible' if db_exists else 'not found',
                'timestamp': datetime.now().isoformat(),
                'service': 'lokerpuller'
            }
            
            self.wfile.write(json.dumps(health_status).encode())
        else:
            self.send_response(404)
            self.end_headers()

# Start health check server
httpd = socketserver.TCPServer(('', 8080), HealthHandler)
server_thread = threading.Thread(target=httpd.serve_forever)
server_thread.daemon = True
server_thread.start()
print('Health check server started on port 8080')

# Keep the main process running
try:
    while True:
        import time
        time.sleep(60)
except KeyboardInterrupt:
    print('Shutting down...')
    httpd.shutdown()
" &

echo "✅ LokerPuller started successfully!"
echo "📊 API: http://localhost:5000"
echo "🏥 Health: http://localhost:8080/health"

# Keep container running
wait 