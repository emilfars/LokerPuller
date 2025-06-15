"""
Constants and configuration for LokerPuller.
"""

# Southeast Asian countries mapping
SEA_COUNTRIES = {
    'Indonesia': ['Indonesia', 'Jakarta', 'Surabaya', 'Bandung', 'Medan'],
    'Malaysia': ['Malaysia', 'Kuala Lumpur', 'Penang', 'Johor Bahru', 'Selangor'],
    'Thailand': ['Thailand', 'Bangkok', 'Chiang Mai', 'Phuket', 'Pattaya'],
    'Vietnam': ['Vietnam', 'Ho Chi Minh City', 'Hanoi', 'Da Nang', 'Hue'],
    'Singapore': ['Singapore']
}

# Configuration for e2-small optimization
MEMORY_OPTIMIZED_CONFIG = {
    'max_results_per_site': 25,  # Reduced for memory efficiency
    'batch_delay': 10,  # Seconds between batches
    'site_delay': 30,   # Seconds between sites
    'country_delay': 60,  # Seconds between countries
    'max_concurrent_processes': 1,  # Sequential processing only
    'cleanup_frequency': 3,  # Cleanup every 3 operations
}

# Southeast Asian countries with optimized search terms
SEA_SCRAPING_CONFIG = {
    'Indonesia': {
        'location': 'Jakarta, Indonesia',
        'search_terms': ['software engineer', 'developer', 'data analyst'],
        'sites': ['indeed', 'linkedin']
    },
    'Malaysia': {
        'location': 'Kuala Lumpur, Malaysia',
        'search_terms': ['software engineer', 'developer', 'data analyst'],
        'sites': ['indeed', 'linkedin']
    },
    'Thailand': {
        'location': 'Bangkok, Thailand',
        'search_terms': ['software engineer', 'developer', 'data analyst'],
        'sites': ['indeed', 'linkedin']
    },
    'Vietnam': {
        'location': 'Ho Chi Minh City, Vietnam',
        'search_terms': ['software engineer', 'developer', 'data analyst'],
        'sites': ['indeed', 'linkedin']
    },
    'Singapore': {
        'location': 'Singapore',
        'search_terms': ['software engineer', 'developer', 'data analyst', 'product manager'],
        'sites': ['indeed', 'linkedin']
    }
}

# Default database schema
DEFAULT_DB_SCHEMA = '''
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    job_url TEXT NOT NULL,
    job_url_direct TEXT,
    title TEXT,
    company_name TEXT,
    location TEXT,
    job_type TEXT,
    date_posted TEXT,
    interval TEXT,
    min_amount REAL,
    max_amount REAL,
    currency TEXT,
    is_remote INTEGER DEFAULT 0,
    job_level TEXT,
    job_function TEXT,
    company_industry TEXT,
    listing_type TEXT,
    emails TEXT,
    description TEXT,
    company_url TEXT,
    company_url_direct TEXT,
    company_addresses TEXT,
    company_num_employees TEXT,
    company_revenue TEXT,
    company_description TEXT,
    logo_photo_url TEXT,
    banner_photo_url TEXT,
    ceo_name TEXT,
    ceo_photo_url TEXT,
    compensation_interval TEXT,
    salary_source TEXT,
    company_rating REAL,
    skills TEXT,
    experience_range TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_url, site)
)
'''

# Database indexes for performance
DB_INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_site ON jobs(site)',
    'CREATE INDEX IF NOT EXISTS idx_location ON jobs(location)',
    'CREATE INDEX IF NOT EXISTS idx_scraped_at ON jobs(scraped_at)',
    'CREATE INDEX IF NOT EXISTS idx_company ON jobs(company_name)',
    'CREATE INDEX IF NOT EXISTS idx_title ON jobs(title)',
] 