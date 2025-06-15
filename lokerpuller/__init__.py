"""
LokerPuller - Southeast Asian Job Scraper

A comprehensive job scraping and management system focused on Southeast Asian markets.
Supports Indonesia, Malaysia, Thailand, Vietnam, and Singapore job markets.
"""

__version__ = "2.0.0"
__author__ = "LokerPuller Team"
__description__ = "Southeast Asian Job Scraper and Management System"

# Core imports
from .core.scraper import JobScraper
from .core.scheduler import JobScheduler
from .database.manager import DatabaseManager

__all__ = [
    "JobScraper",
    "JobScheduler", 
    "DatabaseManager",
] 