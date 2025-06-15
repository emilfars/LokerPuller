FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install the package
RUN pip install -e .

# Make startup script executable
RUN chmod +x startup.sh

# Create directory for logs and database
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV DB_PATH=/app/data/jobs.db
ENV LOG_PATH=/app/logs

# Expose ports (health check and API)
EXPOSE 8080 5000

# Start the application
CMD ["./startup.sh"] 