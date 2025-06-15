#!/bin/bash

# JobSpy GCP Deployment Script
# This script deploys the JobSpy application to Google Cloud Platform

set -e

# Configuration variables
PROJECT_ID="${GCP_PROJECT_ID:-jobspy-scraper}"
REGION="${GCP_REGION:-asia-southeast1}"
ZONE="${GCP_ZONE:-asia-southeast1-a}"
INSTANCE_NAME="${INSTANCE_NAME:-jobspy-scraper}"
MACHINE_TYPE="${MACHINE_TYPE:-e2-standard-2}"
IMAGE_FAMILY="cos-stable"
IMAGE_PROJECT="cos-cloud"
DISK_SIZE="50GB"
DISK_TYPE="pd-standard"

# Docker image configuration
IMAGE_NAME="jobspy-scraper"
IMAGE_TAG="latest"
REGISTRY_URL="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

# Authenticate with GCP
authenticate() {
    print_status "Authenticating with GCP..."
    
    # Check if already authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_status "Please authenticate with GCP:"
        gcloud auth login
    fi
    
    # Set project
    gcloud config set project $PROJECT_ID
    print_status "Using project: $PROJECT_ID"
}

# Enable required APIs
enable_apis() {
    print_status "Enabling required GCP APIs..."
    
    gcloud services enable compute.googleapis.com
    gcloud services enable containerregistry.googleapis.com
    gcloud services enable logging.googleapis.com
    gcloud services enable monitoring.googleapis.com
    
    print_status "APIs enabled successfully"
}

# Build and push Docker image
build_and_push_image() {
    print_status "Building Docker image..."
    
    # Build the image
    docker build -t $IMAGE_NAME:$IMAGE_TAG .
    
    # Tag for GCR
    docker tag $IMAGE_NAME:$IMAGE_TAG $REGISTRY_URL
    
    # Configure Docker to use gcloud as credential helper
    gcloud auth configure-docker --quiet
    
    # Push to GCR
    print_status "Pushing image to Google Container Registry..."
    docker push $REGISTRY_URL
    
    print_status "Image pushed successfully: $REGISTRY_URL"
}

# Create firewall rules
create_firewall_rules() {
    print_status "Creating firewall rules..."
    
    # Allow health check traffic
    if ! gcloud compute firewall-rules describe jobspy-health-check --quiet &> /dev/null; then
        gcloud compute firewall-rules create jobspy-health-check \
            --direction=INGRESS \
            --priority=1000 \
            --network=default \
            --action=ALLOW \
            --rules=tcp:8080 \
            --source-ranges=0.0.0.0/0 \
            --target-tags=jobspy-scraper
    fi
    
    # Allow SSH
    if ! gcloud compute firewall-rules describe jobspy-ssh --quiet &> /dev/null; then
        gcloud compute firewall-rules create jobspy-ssh \
            --direction=INGRESS \
            --priority=1000 \
            --network=default \
            --action=ALLOW \
            --rules=tcp:22 \
            --source-ranges=0.0.0.0/0 \
            --target-tags=jobspy-scraper
    fi
    
    print_status "Firewall rules created"
}

# Create and configure the VM instance
create_instance() {
    print_status "Creating VM instance: $INSTANCE_NAME"
    
    # Create startup script
    cat > startup-script.sh << 'EOF'
#!/bin/bash

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker $USER

# Configure Docker daemon
cat > /etc/docker/daemon.json << 'DOCKER_EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  }
}
DOCKER_EOF

systemctl restart docker
systemctl enable docker

# Authenticate Docker with GCR
gcloud auth configure-docker --quiet

# Create persistent directories
mkdir -p /opt/jobspy/{data,logs}
chmod 755 /opt/jobspy/{data,logs}

# Create Docker Compose file
cat > /opt/jobspy/docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  jobspy:
    image: gcr.io/PROJECT_ID/jobspy-scraper:latest
    container_name: jobspy-scraper
    restart: unless-stopped
    
    environment:
      - DB_PATH=/app/data/jobs.db
      - LOG_PATH=/app/logs
      - TZ=Asia/Singapore
    
    volumes:
      - /opt/jobspy/data:/app/data
      - /opt/jobspy/logs:/app/logs
    
    ports:
      - "8080:8080"
    
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
COMPOSE_EOF

# Replace PROJECT_ID placeholder
sed -i "s/PROJECT_ID/$PROJECT_ID/g" /opt/jobspy/docker-compose.yml

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Pull and start the application
cd /opt/jobspy
docker-compose pull
docker-compose up -d

# Create log rotation configuration
cat > /etc/logrotate.d/jobspy << 'LOGROTATE_EOF'
/opt/jobspy/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
LOGROTATE_EOF

# Install monitoring agent
curl -sSO https://dl.google.com/cloudagents/add-monitoring-agent-repo.sh
bash add-monitoring-agent-repo.sh --also-install

# Create health check script
cat > /opt/jobspy/health-check.sh << 'HEALTH_EOF'
#!/bin/bash
curl -f http://localhost:8080/health || exit 1
EOF

chmod +x /opt/jobspy/health-check.sh

echo "Startup script completed" >> /var/log/startup.log
EOF

    # Replace PROJECT_ID in startup script
    sed -i "s/\$PROJECT_ID/$PROJECT_ID/g" startup-script.sh
    
    # Create the instance
    gcloud compute instances create $INSTANCE_NAME \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --network-interface=network-tier=PREMIUM,subnet=default \
        --maintenance-policy=MIGRATE \
        --provisioning-model=STANDARD \
        --service-account=$(gcloud iam service-accounts list --format="value(email)" --filter="displayName:Compute Engine default service account") \
        --scopes=https://www.googleapis.com/auth/cloud-platform \
        --tags=jobspy-scraper \
        --create-disk=auto-delete=yes,boot=yes,device-name=$INSTANCE_NAME,image=projects/$IMAGE_PROJECT/global/images/family/$IMAGE_FAMILY,mode=rw,size=$DISK_SIZE,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/$DISK_TYPE \
        --metadata-from-file startup-script=startup-script.sh \
        --reservation-affinity=any
    
    print_status "VM instance created: $INSTANCE_NAME"
    
    # Clean up startup script
    rm startup-script.sh
}

# Get instance information
get_instance_info() {
    print_status "Getting instance information..."
    
    EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    INTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].networkIP)')
    
    echo ""
    echo "=== DEPLOYMENT COMPLETED ==="
    echo "Instance Name: $INSTANCE_NAME"
    echo "Zone: $ZONE"
    echo "External IP: $EXTERNAL_IP"
    echo "Internal IP: $INTERNAL_IP"
    echo "Health Check: http://$EXTERNAL_IP:8080/health"
    echo ""
    echo "SSH Command: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE"
    echo "View Logs: gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='docker logs jobspy-scraper'"
    echo ""
    echo "The application may take a few minutes to start up completely."
    echo "Monitor the startup progress with:"
    echo "gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command='tail -f /var/log/startup.log'"
}

# Main deployment function
main() {
    print_status "Starting JobSpy GCP deployment..."
    
    check_prerequisites
    authenticate
    enable_apis
    build_and_push_image
    create_firewall_rules
    create_instance
    
    sleep 30  # Wait for instance to start
    get_instance_info
    
    print_status "Deployment completed successfully!"
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Environment variables:"
    echo "  GCP_PROJECT_ID    - GCP project ID (default: jobspy-scraper)"
    echo "  GCP_REGION        - GCP region (default: asia-southeast1)"
    echo "  GCP_ZONE          - GCP zone (default: asia-southeast1-a)"
    echo "  INSTANCE_NAME     - VM instance name (default: jobspy-scraper)"
    echo "  MACHINE_TYPE      - VM machine type (default: e2-standard-2)"
    echo ""
    echo "Examples:"
    echo "  GCP_PROJECT_ID=my-project $0"
    echo "  GCP_ZONE=asia-southeast1-b MACHINE_TYPE=e2-medium $0"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_usage
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac 