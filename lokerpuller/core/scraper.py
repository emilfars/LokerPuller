"""
Core job scraper for LokerPuller.

Handles job scraping from multiple sites with enhanced logging and SEA country filtering.
"""

import sys
import os
import time
import gc
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add jobspy to path if needed
try:
    from jobspy import scrape_jobs
except ImportError:
    # Try to add jobspy directory to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    jobspy_path = os.path.join(project_root, 'jobspy')
    if os.path.exists(jobspy_path):
        sys.path.append(project_root)
        from jobspy import scrape_jobs
    else:
        raise ImportError("jobspy package not found. Please install it first.")

from ..database.manager import DatabaseManager
from ..utils.logging import get_logger, log_system_resources
from ..utils.validation import validate_sea_country, validate_search_params
from ..utils.constants import SEA_COUNTRIES, MEMORY_OPTIMIZED_CONFIG
from ..config.settings import get_settings


class JobScraper:
    """Main job scraper class for LokerPuller."""
    
    def __init__(self):
        """Initialize the job scraper."""
        self.logger = get_logger("Scraper")
        self.settings = get_settings()
        self.db_manager = DatabaseManager(self.settings.db_path)
        
    def scrape_site_with_logging(
        self, 
        site: str, 
        search_term: str, 
        location: str, 
        results_wanted: int,
        job_type: Optional[str] = None, 
        hours_old: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape a single job site with detailed logging.
        
        Args:
            site: Job site name (indeed, linkedin)
            search_term: Search term for jobs
            location: Location to search in
            results_wanted: Number of results to fetch
            job_type: Optional job type filter
            hours_old: Optional hours filter
            
        Returns:
            List of job dictionaries
        """
        self.logger.info(f"🌐 Starting scrape from {site.upper()}")
        self.logger.info(f"🔍 Search term: '{search_term}'")
        self.logger.info(f"📍 Location: {location}")
        self.logger.info(f"📊 Target results: {results_wanted}")
        
        if job_type:
            self.logger.info(f"💼 Job type filter: {job_type}")
        if hours_old:
            self.logger.info(f"⏰ Hours old filter: {hours_old}")
        
        start_time = time.time()
        
        try:
            # Log system resources before scraping
            log_system_resources(self.logger)
            
            # Perform the scraping
            self.logger.info(f"🚀 Initiating scrape from {site}...")
            
            jobs_df = scrape_jobs(
                site_name=[site],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                job_type=job_type,
                hours_old=hours_old,
                country_indeed='Singapore' if 'singapore' in location.lower() else None,
                verbose=0  # Suppress jobspy logs
            )
            
            elapsed_time = time.time() - start_time
            
            if jobs_df is not None and not jobs_df.empty:
                jobs_list = jobs_df.to_dict('records')
                
                # Filter for SEA countries only
                sea_jobs = []
                for job in jobs_list:
                    if job.get('location') and validate_sea_country(job['location']):
                        sea_jobs.append(job)
                
                self.logger.info(f"✅ {site.upper()} scraping completed in {elapsed_time:.1f}s")
                self.logger.info(f"📈 Total jobs found: {len(jobs_list)}")
                self.logger.info(f"🌏 SEA jobs filtered: {len(sea_jobs)}")
                
                if sea_jobs:
                    # Log sample results
                    sample_size = min(3, len(sea_jobs))
                    self.logger.info(f"📋 Sample results from {site}:")
                    for i, job in enumerate(sea_jobs[:sample_size]):
                        company = job.get('company', 'Unknown Company')
                        title = job.get('title', 'Unknown Title')
                        location = job.get('location', 'Unknown Location')
                        self.logger.info(f"   {i+1}. {title} at {company} ({location})")
                
                # Force garbage collection to free memory
                del jobs_df, jobs_list
                gc.collect()
                
                return sea_jobs
            else:
                self.logger.warning(f"⚠️  No jobs found on {site} for '{search_term}' in {location}")
                return []
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"❌ Error scraping {site} after {elapsed_time:.1f}s: {str(e)}")
            return []
    
    def scrape_jobs(
        self,
        search_term: str,
        location: str,
        results_per_site: int = 25,
        sites: Optional[List[str]] = None,
        job_type: Optional[str] = None,
        hours_old: Optional[int] = None
    ) -> int:
        """
        Scrape jobs from multiple sites and store in database.
        
        Args:
            search_term: Job search term
            location: Location to search in
            results_per_site: Number of results per site
            sites: List of sites to scrape
            job_type: Optional job type filter
            hours_old: Optional hours filter
            
        Returns:
            Number of jobs inserted into database
        """
        if sites is None:
            sites = ['indeed', 'linkedin']
        
        # Validate parameters
        is_valid, error_msg = validate_search_params(search_term, location, results_per_site)
        if not is_valid:
            self.logger.error(f"❌ Invalid parameters: {error_msg}")
            raise ValueError(error_msg)
        
        self.logger.info("🚀 LokerPuller Job Scraper Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"🔍 Search Configuration:")
        self.logger.info(f"   Search Term: '{search_term}'")
        self.logger.info(f"   Location: {location}")
        self.logger.info(f"   Results per site: {results_per_site}")
        self.logger.info(f"   Sites: {', '.join(sites)}")
        self.logger.info(f"   Job Type: {job_type or 'Any'}")
        self.logger.info(f"   Hours Old: {hours_old or 'Any'}")
        self.logger.info("=" * 60)
        
        total_start_time = time.time()
        all_jobs = []
        
        for i, site in enumerate(sites):
            self.logger.info(f"📍 Processing site {i+1}/{len(sites)}: {site.upper()}")
            
            # Scrape from site
            site_jobs = self.scrape_site_with_logging(
                site=site,
                search_term=search_term,
                location=location,
                results_wanted=results_per_site,
                job_type=job_type,
                hours_old=hours_old
            )
            
            if site_jobs:
                all_jobs.extend(site_jobs)
                self.logger.info(f"✅ Added {len(site_jobs)} jobs from {site}")
            else:
                self.logger.warning(f"⚠️  No jobs added from {site}")
            
            # Memory optimization: delay between sites
            if i < len(sites) - 1:  # Don't delay after last site
                delay = MEMORY_OPTIMIZED_CONFIG['site_delay']
                self.logger.info(f"⏳ Waiting {delay}s before next site...")
                time.sleep(delay)
                
                # Force garbage collection
                gc.collect()
        
        total_elapsed = time.time() - total_start_time
        
        self.logger.info("=" * 60)
        self.logger.info(f"📊 Scraping Summary:")
        self.logger.info(f"   Total jobs scraped: {len(all_jobs)}")
        self.logger.info(f"   Total time: {total_elapsed:.1f}s")
        self.logger.info(f"   Average per site: {total_elapsed/len(sites):.1f}s")
        
        # Insert jobs into database
        if all_jobs:
            inserted_count = self.db_manager.insert_jobs(all_jobs)
            self.logger.info(f"💾 Database insertion completed: {inserted_count} new jobs")
            
            # Log final system resources
            log_system_resources(self.logger)
            
            return inserted_count
        else:
            self.logger.warning("⚠️  No jobs to insert into database")
            return 0 