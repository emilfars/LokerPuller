"""
Basic import tests for LokerPuller.
"""

import pytest


def test_core_imports():
    """Test that core modules can be imported."""
    from lokerpuller.core.scraper import JobScraper
    from lokerpuller.core.scheduler import JobScheduler
    
    assert JobScraper is not None
    assert JobScheduler is not None


def test_database_imports():
    """Test that database modules can be imported."""
    from lokerpuller.database.manager import DatabaseManager
    from lokerpuller.database.models import Job
    
    assert DatabaseManager is not None
    assert Job is not None


def test_utils_imports():
    """Test that utility modules can be imported."""
    from lokerpuller.utils.constants import SEA_COUNTRIES
    from lokerpuller.utils.validation import validate_sea_country
    from lokerpuller.utils.logging import get_logger
    
    assert SEA_COUNTRIES is not None
    assert validate_sea_country is not None
    assert get_logger is not None


def test_api_imports():
    """Test that API modules can be imported."""
    from lokerpuller.api.app import create_app
    
    assert create_app is not None


def test_config_imports():
    """Test that config modules can be imported."""
    from lokerpuller.config.settings import get_settings
    
    assert get_settings is not None


def test_cli_imports():
    """Test that CLI module can be imported."""
    from lokerpuller.cli import main
    
    assert main is not None 