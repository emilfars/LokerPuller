"""
LokerPuller REST API

Flask API for job board frontend with filtering, sorting, and manual scraping capabilities.
"""

import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

from ..database.manager import DatabaseManager
from ..core.scraper import JobScraper
from ..utils.logging import get_logger
from ..config.settings import get_settings


def create_app() -> Flask:
    """Create and configure the Flask application."""
    settings = get_settings()
    
    # Create Flask app with proper template and static folders
    template_folder = os.path.join(os.path.dirname(__file__), '..', 'web', 'templates')
    static_folder = os.path.join(os.path.dirname(__file__), '..', 'web', 'static')
    
    app = Flask(__name__, 
                template_folder=template_folder, 
                static_folder=static_folder)
    CORS(app)  # Enable CORS for frontend requests
    
    # Setup logging
    logger = get_logger("API")
    
    # Initialize components
    db_manager = DatabaseManager(settings.db_path)
    scraper = JobScraper()
    
    @app.route('/')
    def index():
        """Serve the main job board page."""
        return render_template('index.html')
    
    @app.route('/api/jobs')
    def get_jobs():
        """Get jobs with filtering and pagination."""
        try:
            # Parse query parameters
            filters = {
                'title': request.args.get('title'),
                'company': request.args.get('company'),
                'location': request.args.get('location'),
                'country': request.args.get('country'),
                'job_type': request.args.get('job_type'),
                'site': request.args.get('site'),
                'is_remote': request.args.get('is_remote'),
                'min_salary': request.args.get('min_salary'),
                'max_salary': request.args.get('max_salary'),
                'days_old': request.args.get('days_old'),
                'sort_by': request.args.get('sort_by', 'scraped_at'),
                'sort_order': request.args.get('sort_order', 'desc')
            }
            
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}
            
            # Parse pagination
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), settings.max_results_per_request)
            
            # Search jobs
            jobs, total_count = db_manager.search_jobs(filters, page, per_page)
            
            # Format jobs for display
            formatted_jobs = []
            for job in jobs:
                # Format salary display
                if job.get('min_amount') and job.get('max_amount'):
                    job['salary_display'] = f"{job.get('currency', 'USD')} {job['min_amount']:,.0f} - {job['max_amount']:,.0f}"
                elif job.get('min_amount'):
                    job['salary_display'] = f"{job.get('currency', 'USD')} {job['min_amount']:,.0f}+"
                else:
                    job['salary_display'] = "Not specified"
                
                # Format dates
                if job.get('date_posted'):
                    try:
                        if isinstance(job['date_posted'], str):
                            job['date_posted_formatted'] = datetime.strptime(job['date_posted'], '%Y-%m-%d').strftime('%B %d, %Y')
                        else:
                            job['date_posted_formatted'] = job['date_posted'].strftime('%B %d, %Y')
                    except:
                        job['date_posted_formatted'] = job['date_posted']
                else:
                    job['date_posted_formatted'] = "Not specified"
                
                if job.get('scraped_at'):
                    try:
                        if isinstance(job['scraped_at'], str):
                            job['scraped_at_formatted'] = datetime.strptime(job['scraped_at'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y at %I:%M %p')
                        else:
                            job['scraped_at_formatted'] = job['scraped_at'].strftime('%B %d, %Y at %I:%M %p')
                    except:
                        job['scraped_at_formatted'] = job['scraped_at']
                
                formatted_jobs.append(job)
            
            # Calculate pagination
            total_pages = (total_count + per_page - 1) // per_page
            
            return jsonify({
                'jobs': formatted_jobs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'filters': filters
            })
            
        except Exception as e:
            logger.error(f"Error in get_jobs: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/jobs/stats')
    def get_job_stats():
        """Get database statistics."""
        try:
            stats = db_manager.get_statistics()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Error in get_job_stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/jobs/filters')
    def get_filter_options():
        """Get available filter options."""
        try:
            options = db_manager.get_filter_options()
            return jsonify(options)
        except Exception as e:
            logger.error(f"Error in get_filter_options: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/scrape', methods=['POST'])
    def trigger_scraping():
        """Trigger manual job scraping."""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            search_term = data.get('search_term')
            location = data.get('location') or data.get('country', 'Singapore')
            results = min(int(data.get('results', 25)), settings.max_results_per_request)
            sites = data.get('sites', ['indeed', 'linkedin'])
            job_type = data.get('job_type')
            
            if not search_term:
                return jsonify({'error': 'search_term is required'}), 400
            
            logger.info(f"Manual scraping triggered: {search_term} in {location}")
            
            def run_scraping():
                """Run scraping in background thread."""
                try:
                    inserted_count = scraper.scrape_jobs(
                        search_term=search_term,
                        location=location,
                        results_per_site=results,
                        sites=sites,
                        job_type=job_type
                    )
                    logger.info(f"Manual scraping completed: {inserted_count} jobs inserted")
                except Exception as e:
                    logger.error(f"Manual scraping failed: {e}")
            
            # Start scraping in background
            thread = threading.Thread(target=run_scraping)
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'message': 'Scraping started successfully',
                'search_term': search_term,
                'location': location,
                'results': results,
                'sites': sites
            })
            
        except Exception as e:
            logger.error(f"Error in trigger_scraping: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint."""
        try:
            # Check database connection
            stats = db_manager.get_statistics()
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': {
                    'connected': True,
                    'total_jobs': stats.get('total_jobs', 0)
                },
                'version': '2.0.0'
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files."""
        return send_from_directory(app.static_folder, filename)
    
    def print_startup_info():
        """Print startup information."""
        print("🚀 LokerPuller API Server Starting...")
        print("=" * 60)
        print(f"📍 Server: http://{settings.api_host}:{settings.api_port}")
        print(f"🗄️  Database: {settings.db_path}")
        print(f"📝 Logs: {settings.log_path}")
        print("")
        print("🌐 Available URLs:")
        print(f"   Web Interface: http://{settings.api_host}:{settings.api_port}")
        print(f"   API Base: http://{settings.api_host}:{settings.api_port}/api/")
        print(f"   Health Check: http://{settings.api_host}:{settings.api_port}/api/health")
        print("")
        print("🔧 API Endpoints:")
        print(f"   GET  /api/jobs          - Search jobs")
        print(f"   GET  /api/jobs/stats    - Database statistics")
        print(f"   GET  /api/jobs/filters  - Filter options")
        print(f"   POST /api/scrape        - Manual scraping")
        print(f"   GET  /api/health        - Health check")
        print("")
        print("📊 Usage Examples:")
        print(f"   curl http://{settings.api_host}:{settings.api_port}/api/health")
        print(f"   curl http://{settings.api_host}:{settings.api_port}/api/jobs?title=python")
        print("=" * 60)
        print("✅ Server ready! Open your browser to start browsing jobs.")
        print("")
    
    # Print startup info when app is created
    print_startup_info()
    
    return app


def main():
    """Main function to run the API server."""
    settings = get_settings()
    app = create_app()
    
    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=settings.api_debug
    )


if __name__ == "__main__":
    main() 