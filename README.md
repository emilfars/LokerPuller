# LokerPuller 🚀

**Professional Southeast Asian Job Scraper and Management System**

LokerPuller is a production-ready job scraping and management system designed for Southeast Asian markets. It efficiently scrapes job postings from major job boards and provides a modern web interface for browsing opportunities across Indonesia, Malaysia, Thailand, Vietnam, and Singapore.

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()

## ✨ Key Features

- 🌏 **SEA-Focused**: Targets Indonesia, Malaysia, Thailand, Vietnam, and Singapore
- 🔍 **Multi-Platform**: Scrapes Indeed and LinkedIn job boards
- 💻 **Modern Web UI**: Responsive interface with advanced filtering
- 📊 **Analytics**: Real-time statistics and insights
- 🚀 **RESTful API**: Programmatic access to job data
- ⚡ **Optimized**: Memory-efficient for cloud deployment
- 🔄 **Automated**: Scheduled scraping with resource management
- 📱 **Mobile-Ready**: Works seamlessly on all devices

## 🏗️ Architecture

```
lokerpuller/
├── lokerpuller/           # Main package
│   ├── core/             # Scraping & scheduling logic
│   ├── api/              # Flask REST API
│   ├── database/         # Data management
│   ├── utils/            # Utilities & validation
│   ├── config/           # Settings management
│   └── web/              # Frontend assets
├── jobspy/               # Core scraping engine
├── data/                 # Database storage
└── logs/                 # Application logs
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/your-username/lokerpuller.git
cd lokerpuller

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Basic Usage

```bash
# Start web interface
lokerpuller api

# Scrape jobs
lokerpuller scrape --search-term "software engineer" --location "Singapore" --results 25

# View help
lokerpuller --help
```

## 📖 Usage Guide

### Web Interface

Start the web application:
```bash
lokerpuller api --host 0.0.0.0 --port 5000
```

Access at: `http://localhost:5000`

### Command Line Interface

**Scrape Jobs:**
```bash
lokerpuller scrape \
  --search-term "python developer" \
  --location "Jakarta, Indonesia" \
  --results 50 \
  --sites indeed linkedin
```

**Schedule Operations:**
```bash
lokerpuller schedule daily    # Daily scraping
lokerpuller schedule cleanup  # Database cleanup
```

### Python API

```python
from lokerpuller.core.scraper import JobScraper
from lokerpuller.database.manager import DatabaseManager

# Initialize scraper
scraper = JobScraper()

# Scrape jobs
jobs_count = scraper.scrape_jobs(
    search_term="data scientist",
    location="Singapore",
    results_per_site=25
)

# Access database
db = DatabaseManager("data/jobs.db")
jobs, total = db.search_jobs({"title": "engineer"}, page=1, per_page=20)
```

### REST API

**Get Jobs:**
```bash
curl "http://localhost:5000/api/jobs?title=engineer&location=Singapore&page=1&per_page=20"
```

**Get Statistics:**
```bash
curl "http://localhost:5000/api/stats"
```

**Search with Filters:**
```bash
curl "http://localhost:5000/api/jobs?company=Google&job_type=full-time&is_remote=true"
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t lokerpuller .

# Run container
docker run -d \
  --name lokerpuller \
  -p 5000:5000 \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  lokerpuller
```

### Docker Compose

```yaml
version: '3.8'
services:
  lokerpuller:
    build: .
    ports:
      - "5000:5000"
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DB_PATH=/app/data/jobs.db
      - LOG_PATH=/app/logs
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```env
# Database
DB_PATH=data/jobs.db

# API Settings
API_HOST=0.0.0.0
API_PORT=5000
API_DEBUG=false

# Scraping
MAX_RESULTS_PER_SITE=25
BATCH_DELAY=10
SITE_DELAY=30

# Logging
LOG_LEVEL=INFO
LOG_PATH=logs/
```

### Settings Management

```python
from lokerpuller.config.settings import get_settings, update_settings

# Get current settings
settings = get_settings()

# Update settings
update_settings(api_port=8000, max_results_per_site=50)
```

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Test deployment
./test-deployment.sh

# Check code quality
black lokerpuller/
isort lokerpuller/
flake8 lokerpuller/
```

## 📊 Performance

- **Memory Usage**: ~200MB (optimized for e2-small instances)
- **Scraping Speed**: ~25 jobs/minute per site
- **Database**: SQLite with optimized indexes
- **API Response**: <100ms for most queries

## 🔧 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run in development mode
lokerpuller api --debug
```

### Project Structure

- `lokerpuller/core/`: Business logic (scraping, scheduling)
- `lokerpuller/api/`: REST API endpoints
- `lokerpuller/database/`: Data models and operations
- `lokerpuller/utils/`: Utilities and validation
- `lokerpuller/config/`: Configuration management
- `jobspy/`: Core scraping engine

## 🚀 Deployment

### Cloud Deployment

The application is optimized for cloud deployment:

```bash
# Google Cloud Platform
./deploy-gcp.sh

# AWS/Azure
docker build -t lokerpuller .
# Push to your container registry
```

### Production Considerations

- Use environment variables for configuration
- Set up proper logging and monitoring
- Configure database backups
- Use reverse proxy (nginx) for production
- Set up SSL certificates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run quality checks: `black`, `isort`, `flake8`
5. Commit changes: `git commit -am 'Add feature'`
6. Push to branch: `git push origin feature-name`
7. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/lokerpuller/issues)
- **Documentation**: [Project Wiki](https://github.com/your-username/lokerpuller/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/lokerpuller/discussions)

## 🙏 Acknowledgments

- Built on top of [JobSpy](https://github.com/cullenwatson/JobSpy) scraping engine
- Inspired by the need for SEA-focused job aggregation
- Thanks to all contributors and users

---

**Made with ❤️ for the Southeast Asian tech community**

🚀 **Ready to find your next opportunity in Southeast Asia!**
