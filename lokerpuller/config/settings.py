"""
Settings and configuration management for LokerPuller.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings."""
    
    # Database settings
    db_path: str = "./data/jobs.db"
    
    # Logging settings
    log_path: str = "./logs"
    log_level: str = "INFO"
    
    # API settings
    api_host: str = "127.0.0.1"
    api_port: int = 5000
    api_debug: bool = False
    
    # Scraping settings
    default_results_per_site: int = 25
    max_results_per_request: int = 200
    scraping_timeout: int = 1800  # 30 minutes
    
    # Memory optimization settings
    batch_size: int = 50
    batch_delay: int = 10
    site_delay: int = 30
    country_delay: int = 60
    
    # Cleanup settings
    cleanup_days: int = 14
    log_retention_days: int = 7
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls(
            db_path=os.getenv("DB_PATH", "./data/jobs.db"),
            log_path=os.getenv("LOG_PATH", "./logs"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            api_host=os.getenv("API_HOST", "127.0.0.1"),
            api_port=int(os.getenv("API_PORT", "5000")),
            api_debug=os.getenv("API_DEBUG", "false").lower() == "true",
            default_results_per_site=int(os.getenv("DEFAULT_RESULTS_PER_SITE", "25")),
            max_results_per_request=int(os.getenv("MAX_RESULTS_PER_REQUEST", "200")),
            scraping_timeout=int(os.getenv("SCRAPING_TIMEOUT", "1800")),
            batch_size=int(os.getenv("BATCH_SIZE", "50")),
            batch_delay=int(os.getenv("BATCH_DELAY", "10")),
            site_delay=int(os.getenv("SITE_DELAY", "30")),
            country_delay=int(os.getenv("COUNTRY_DELAY", "60")),
            cleanup_days=int(os.getenv("CLEANUP_DAYS", "14")),
            log_retention_days=int(os.getenv("LOG_RETENTION_DAYS", "7")),
        )
    
    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        # Create data directory
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log directory
        log_dir = Path(self.log_path)
        log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_db_url(self) -> str:
        """Get database URL."""
        return f"sqlite:///{self.db_path}"
    
    def get_log_file(self, component: str) -> str:
        """Get log file path for a component."""
        return os.path.join(self.log_path, f"{component}.log")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
        _settings.ensure_directories()
    return _settings


def update_settings(**kwargs) -> None:
    """Update global settings."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    
    for key, value in kwargs.items():
        if hasattr(_settings, key):
            setattr(_settings, key, value)
    
    _settings.ensure_directories() 