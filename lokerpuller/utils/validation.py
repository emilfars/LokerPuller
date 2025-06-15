"""
Validation utilities for LokerPuller.
"""

from .constants import SEA_COUNTRIES


def validate_sea_country(location: str) -> bool:
    """
    Validate if location is in Southeast Asia.
    
    Args:
        location: Location string to validate
        
    Returns:
        True if location is in SEA, False otherwise
    """
    if not location:
        return False
        
    location_lower = location.lower()
    for country, cities in SEA_COUNTRIES.items():
        for city in cities:
            if city.lower() in location_lower:
                return True
    return False


def get_sea_location_for_scraping(country: str) -> str:
    """
    Get the best location string for scraping from a SEA country.
    
    Args:
        country: Country name
        
    Returns:
        Optimized location string for scraping
    """
    location_map = {
        'Indonesia': 'Jakarta, Indonesia',
        'Malaysia': 'Kuala Lumpur, Malaysia', 
        'Thailand': 'Bangkok, Thailand',
        'Vietnam': 'Ho Chi Minh City, Vietnam',
        'Singapore': 'Singapore'
    }
    return location_map.get(country, country)


def validate_search_params(search_term: str, location: str, results: int) -> tuple[bool, str]:
    """
    Validate search parameters.
    
    Args:
        search_term: Job search term
        location: Job location
        results: Number of results requested
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not search_term or not search_term.strip():
        return False, "Search term cannot be empty"
    
    if not location or not location.strip():
        return False, "Location cannot be empty"
    
    if results <= 0:
        return False, "Results must be greater than 0"
    
    if results > 200:
        return False, "Results cannot exceed 200"
    
    # Check if location is in SEA
    if not any(country.lower() in location.lower() for country in SEA_COUNTRIES.keys()):
        return False, f"Location must be in Southeast Asia: {', '.join(SEA_COUNTRIES.keys())}"
    
    return True, ""


def sanitize_job_data(job_data: dict) -> dict:
    """
    Sanitize and validate job data.
    
    Args:
        job_data: Raw job data dictionary
        
    Returns:
        Sanitized job data dictionary
    """
    sanitized = {}
    
    # Required fields
    sanitized['site'] = str(job_data.get('site', '')).strip()
    sanitized['job_url'] = str(job_data.get('job_url', '')).strip()
    sanitized['title'] = str(job_data.get('title', '')).strip()
    
    # Optional string fields
    string_fields = [
        'job_url_direct', 'company_name', 'location', 'job_type', 'date_posted',
        'interval', 'currency', 'job_level', 'job_function', 'company_industry',
        'listing_type', 'emails', 'description', 'company_url', 'company_url_direct',
        'company_addresses', 'company_num_employees', 'company_revenue',
        'company_description', 'logo_photo_url', 'banner_photo_url', 'ceo_name',
        'ceo_photo_url', 'compensation_interval', 'salary_source', 'skills',
        'experience_range'
    ]
    
    for field in string_fields:
        value = job_data.get(field)
        sanitized[field] = str(value).strip() if value is not None else None
    
    # Numeric fields
    numeric_fields = ['min_amount', 'max_amount', 'company_rating']
    for field in numeric_fields:
        value = job_data.get(field)
        if value is not None:
            try:
                sanitized[field] = float(value)
            except (ValueError, TypeError):
                sanitized[field] = None
        else:
            sanitized[field] = None
    
    # Boolean field
    is_remote = job_data.get('is_remote')
    if isinstance(is_remote, bool):
        sanitized['is_remote'] = 1 if is_remote else 0
    elif isinstance(is_remote, (int, str)):
        sanitized['is_remote'] = 1 if str(is_remote).lower() in ('true', '1', 'yes') else 0
    else:
        sanitized['is_remote'] = 0
    
    return sanitized 