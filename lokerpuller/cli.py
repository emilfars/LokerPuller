"""
Command line interface for LokerPuller.
"""

import sys
import argparse
from typing import Optional

from .core.scraper import JobScraper
from .core.scheduler import JobScheduler
from .api.app import create_app
from .config.settings import get_settings
from .utils.logging import setup_logging


def run_scraper(args) -> int:
    """Run the job scraper."""
    try:
        scraper = JobScraper()
        result = scraper.scrape_jobs(
            search_term=args.search_term,
            location=args.location,
            results_per_site=args.results,
            sites=args.sites,
            job_type=args.job_type,
            hours_old=args.hours_old
        )
        print(f"✅ Scraping completed successfully. Inserted {result} jobs.")
        return 0
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return 1


def run_scheduler(args) -> int:
    """Run the job scheduler."""
    try:
        scheduler = JobScheduler()
        
        if args.command == 'daily':
            scheduler.run_daily_scraping()
        elif args.command == 'weekly':
            scheduler.run_weekly_maintenance()
        elif args.command == 'cleanup':
            scheduler.run_cleanup()
        
        return 0
    except Exception as e:
        print(f"❌ Scheduler failed: {e}")
        return 1


def run_api(args) -> int:
    """Run the API server."""
    try:
        settings = get_settings()
        app = create_app()
        
        app.run(
            host=settings.api_host,
            port=settings.api_port,
            debug=settings.api_debug
        )
        return 0
    except Exception as e:
        print(f"❌ API server failed: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='LokerPuller - Southeast Asian Job Scraper',
        prog='lokerpuller'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scraper command
    scraper_parser = subparsers.add_parser('scrape', help='Run job scraper')
    scraper_parser.add_argument('--search-term', required=True, help='Job search term')
    scraper_parser.add_argument('--location', required=True, help='Job location (SEA country)')
    scraper_parser.add_argument('--results', type=int, default=25, help='Number of results per site')
    scraper_parser.add_argument('--sites', nargs='+', default=['indeed', 'linkedin'], 
                               help='Job sites to scrape')
    scraper_parser.add_argument('--job-type', help='Job type filter')
    scraper_parser.add_argument('--hours-old', type=int, help='Maximum job age in hours')
    scraper_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    scraper_parser.set_defaults(func=run_scraper)
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser('schedule', help='Run job scheduler')
    scheduler_parser.add_argument('command', choices=['daily', 'weekly', 'cleanup'], 
                                 help='Scheduler command to run')
    scheduler_parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    scheduler_parser.set_defaults(func=run_scheduler)
    
    # API command
    api_parser = subparsers.add_parser('api', help='Run API server')
    api_parser.add_argument('--host', help='API host address')
    api_parser.add_argument('--port', type=int, help='API port number')
    api_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    api_parser.set_defaults(func=run_api)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging if verbose
    if hasattr(args, 'verbose') and args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update settings if provided
    if args.command == 'api':
        from .config.settings import update_settings
        updates = {}
        if args.host:
            updates['api_host'] = args.host
        if args.port:
            updates['api_port'] = args.port
        if args.debug:
            updates['api_debug'] = True
        if updates:
            update_settings(**updates)
    
    # Run the command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main()) 