"""
Core job scheduler for LokerPuller.

Handles automated job scraping with memory optimization for e2-small instances.
"""

import os
import sys
import time
import gc
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from ..database.manager import DatabaseManager
from ..utils.logging import get_logger, log_system_resources, cleanup_old_logs
from ..utils.constants import SEA_SCRAPING_CONFIG, MEMORY_OPTIMIZED_CONFIG
from ..config.settings import get_settings
from .scraper import JobScraper


class JobScheduler:
    """Main job scheduler class for LokerPuller."""
    
    def __init__(self):
        """Initialize the job scheduler."""
        self.logger = get_logger("Scheduler")
        self.settings = get_settings()
        self.db_manager = DatabaseManager(self.settings.db_path)
        self.scraper = JobScraper()
        
    def cleanup_memory(self) -> None:
        """Force garbage collection and memory cleanup."""
        self.logger.debug("🧹 Performing memory cleanup...")
        gc.collect()
        time.sleep(2)  # Give system time to cleanup
    
    def run_scraping_job(
        self, 
        country: str, 
        search_term: str, 
        sites: List[str],
        max_results: int = 25
    ) -> bool:
        """
        Run a single scraping job with error handling and logging.
        
        Args:
            country: Country name
            search_term: Job search term
            sites: List of sites to scrape
            max_results: Maximum results per site
            
        Returns:
            True if successful, False otherwise
        """
        if country not in SEA_SCRAPING_CONFIG:
            self.logger.error(f"❌ Unknown country: {country}")
            return False
            
        config = SEA_SCRAPING_CONFIG[country]
        location = config['location']
        
        self.logger.info(f"🌐 Starting scrape: {country}")
        self.logger.info(f"   🔍 Search: '{search_term}'")
        self.logger.info(f"   📍 Location: {location}")
        self.logger.info(f"   🌐 Sites: {', '.join(sites)}")
        self.logger.info(f"   📊 Max results: {max_results}")
        
        start_time = time.time()
        
        try:
            # Use the scraper class directly
            inserted_count = self.scraper.scrape_jobs(
                search_term=search_term,
                location=location,
                results_per_site=max_results,
                sites=sites,
                hours_old=336  # Only jobs from last 2 weeks
            )
            
            elapsed_time = time.time() - start_time
            
            if inserted_count >= 0:  # Success (even if 0 jobs inserted)
                self.logger.info(f"✅ {country} scrape completed successfully")
                self.logger.info(f"   ⏱️  Time: {elapsed_time:.1f} seconds")
                self.logger.info(f"   📈 Jobs inserted: {inserted_count}")
                return True
            else:
                self.logger.error(f"❌ {country} scrape failed")
                self.logger.error(f"   ⏱️  Time: {elapsed_time:.1f} seconds")
                return False
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"❌ {country} scrape failed after {elapsed_time:.1f} seconds: {e}")
            return False
    
    def run_daily_scraping(self) -> Dict[str, int]:
        """
        Run the daily scraping routine optimized for e2-small.
        
        Returns:
            Dictionary with scraping statistics
        """
        self.logger.info("🚀 LokerPuller Daily Scraping Started")
        self.logger.info("=" * 60)
        self.logger.info(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        self.logger.info(f"🌏 Target countries: {', '.join(SEA_SCRAPING_CONFIG.keys())}")
        self.logger.info(f"💾 Memory optimization: Enabled for e2-small")
        self.logger.info("=" * 60)
        
        # Log initial system state
        log_system_resources(self.logger)
        
        total_start_time = time.time()
        successful_jobs = 0
        failed_jobs = 0
        total_jobs = 0
        
        # Process each country sequentially to minimize memory usage
        for country_idx, (country, config) in enumerate(SEA_SCRAPING_CONFIG.items(), 1):
            self.logger.info(f"🌍 Processing country {country_idx}/{len(SEA_SCRAPING_CONFIG)}: {country}")
            
            # Process each search term for the country
            for term_idx, search_term in enumerate(config['search_terms'], 1):
                self.logger.info(f"🔍 Search term {term_idx}/{len(config['search_terms'])}: '{search_term}'")
                
                # Run scraping job
                success = self.run_scraping_job(
                    country=country,
                    search_term=search_term,
                    sites=config['sites'],
                    max_results=MEMORY_OPTIMIZED_CONFIG['max_results_per_site']
                )
                
                total_jobs += 1
                if success:
                    successful_jobs += 1
                else:
                    failed_jobs += 1
                
                # Memory optimization between search terms
                if term_idx < len(config['search_terms']):
                    delay = MEMORY_OPTIMIZED_CONFIG['batch_delay']
                    self.logger.info(f"⏳ Waiting {delay}s before next search term...")
                    time.sleep(delay)
                    self.cleanup_memory()
            
            # Memory optimization between countries
            if country_idx < len(SEA_SCRAPING_CONFIG):
                delay = MEMORY_OPTIMIZED_CONFIG['country_delay']
                self.logger.info(f"⏳ Waiting {delay}s before next country...")
                time.sleep(delay)
                self.cleanup_memory()
                
                # Log system resources periodically
                log_system_resources(self.logger)
        
        total_elapsed = time.time() - total_start_time
        
        # Final summary
        self.logger.info("=" * 60)
        self.logger.info("📊 Daily Scraping Summary:")
        self.logger.info(f"   ⏰ Total time: {total_elapsed/60:.1f} minutes")
        self.logger.info(f"   ✅ Successful jobs: {successful_jobs}/{total_jobs}")
        self.logger.info(f"   ❌ Failed jobs: {failed_jobs}/{total_jobs}")
        self.logger.info(f"   📈 Success rate: {(successful_jobs/total_jobs)*100:.1f}%")
        
        # Get final database stats
        try:
            stats = self.db_manager.get_statistics()
            self.logger.info(f"   🗄️  Total jobs in database: {stats['total_jobs']}")
        except Exception as e:
            self.logger.error(f"❌ Could not get database stats: {e}")
        
        # Final system resources
        log_system_resources(self.logger)
        
        self.logger.info("🏁 Daily scraping completed")
        self.logger.info("=" * 60)
        
        return {
            'total_jobs': total_jobs,
            'successful_jobs': successful_jobs,
            'failed_jobs': failed_jobs,
            'total_time': total_elapsed,
            'success_rate': (successful_jobs/total_jobs)*100 if total_jobs > 0 else 0
        }
    
    def run_weekly_maintenance(self) -> None:
        """Run weekly maintenance tasks."""
        self.logger.info("🔧 LokerPuller Weekly Maintenance Started")
        self.logger.info("=" * 60)
        
        try:
            # Clean up old jobs (older than configured days)
            deleted_count = self.db_manager.cleanup_old_jobs(self.settings.cleanup_days)
            self.logger.info(f"🧹 Cleaned up {deleted_count} old jobs")
            
            # Clean up old logs
            cleanup_old_logs(self.settings.log_path, self.settings.log_retention_days)
            self.logger.info(f"🗂️  Cleaned up old log files")
            
            # Get database statistics
            stats = self.db_manager.get_statistics()
            self.logger.info(f"📊 Database statistics:")
            self.logger.info(f"   Total jobs: {stats['total_jobs']}")
            self.logger.info(f"   Remote jobs: {stats['remote_percentage']:.1f}%")
            
            # Log system resources
            log_system_resources(self.logger)
            
            self.logger.info("✅ Weekly maintenance completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Weekly maintenance failed: {e}")
        
        self.logger.info("=" * 60)
    
    def run_cleanup(self) -> None:
        """Run cleanup tasks."""
        self.logger.info("🧹 LokerPuller Cleanup Started")
        
        try:
            # Force memory cleanup
            self.cleanup_memory()
            
            # Clean up old logs
            cleanup_old_logs(self.settings.log_path, self.settings.log_retention_days)
            
            # Log system resources
            log_system_resources(self.logger)
            
            self.logger.info("✅ Cleanup completed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Cleanup failed: {e}")


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LokerPuller Scheduler')
    parser.add_argument('command', choices=['daily', 'weekly', 'cleanup'], 
                       help='Scheduler command to run')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create scheduler and run command
    scheduler = JobScheduler()
    
    if args.command == 'daily':
        scheduler.run_daily_scraping()
    elif args.command == 'weekly':
        scheduler.run_weekly_maintenance()
    elif args.command == 'cleanup':
        scheduler.run_cleanup()


if __name__ == "__main__":
    main() 