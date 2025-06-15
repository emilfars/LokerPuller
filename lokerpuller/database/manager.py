"""
Database manager for LokerPuller.
"""

import sqlite3
import gc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from ..utils.logging import get_logger
from ..utils.constants import DEFAULT_DB_SCHEMA, DB_INDEXES
from ..utils.validation import validate_sea_country, sanitize_job_data
from .models import Job


class DatabaseManager:
    """Manages database operations for LokerPuller."""
    
    def __init__(self, db_path: str):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = get_logger("DatabaseManager")
        self._ensure_database()
    
    def _ensure_database(self) -> None:
        """Ensure database and tables exist."""
        self.logger.info(f"🗄️  Creating/verifying database at: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create main table
        cursor.execute(DEFAULT_DB_SCHEMA)
        
        # Create indexes
        for index_sql in DB_INDEXES:
            cursor.execute(index_sql)
        
        conn.commit()
        conn.close()
        self.logger.info("✅ Database schema created/verified successfully")
    
    def insert_jobs(self, jobs_data: List[Dict[str, Any]]) -> int:
        """
        Insert job postings into the database.
        
        Args:
            jobs_data: List of job dictionaries
            
        Returns:
            Number of jobs inserted
        """
        if not jobs_data:
            self.logger.warning("⚠️  No jobs data to insert")
            return 0
        
        self.logger.info(f"💾 Inserting {len(jobs_data)} jobs into database...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted_count = 0
        skipped_count = 0
        
        # Process jobs in batches to save memory
        batch_size = 50
        for i in range(0, len(jobs_data), batch_size):
            batch = jobs_data[i:i + batch_size]
            self.logger.debug(f"📦 Processing batch {i//batch_size + 1}/{(len(jobs_data) + batch_size - 1)//batch_size}")
            
            for job_data in batch:
                try:
                    # Validate Southeast Asian location
                    if job_data.get('location') and not validate_sea_country(job_data['location']):
                        self.logger.debug(f"🚫 Skipping job outside SEA: {job_data.get('title', 'Unknown')} at {job_data.get('location', 'Unknown')}")
                        skipped_count += 1
                        continue
                    
                    # Sanitize job data
                    sanitized_job = sanitize_job_data(job_data)
                    
                    # Insert job
                    cursor.execute('''
                        INSERT OR IGNORE INTO jobs (
                            site, job_url, job_url_direct, title, company_name, location,
                            job_type, date_posted, interval, min_amount, max_amount, currency,
                            is_remote, job_level, job_function, company_industry, listing_type,
                            emails, description, company_url, company_url_direct, company_addresses,
                            company_num_employees, company_revenue, company_description,
                            logo_photo_url, banner_photo_url, ceo_name, ceo_photo_url,
                            compensation_interval, salary_source, company_rating, skills, experience_range
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sanitized_job['site'], sanitized_job['job_url'], sanitized_job['job_url_direct'],
                        sanitized_job['title'], sanitized_job['company_name'], sanitized_job['location'],
                        sanitized_job['job_type'], sanitized_job['date_posted'], sanitized_job['interval'],
                        sanitized_job['min_amount'], sanitized_job['max_amount'], sanitized_job['currency'],
                        sanitized_job['is_remote'], sanitized_job['job_level'], sanitized_job['job_function'],
                        sanitized_job['company_industry'], sanitized_job['listing_type'], sanitized_job['emails'],
                        sanitized_job['description'], sanitized_job['company_url'], sanitized_job['company_url_direct'],
                        sanitized_job['company_addresses'], sanitized_job['company_num_employees'],
                        sanitized_job['company_revenue'], sanitized_job['company_description'],
                        sanitized_job['logo_photo_url'], sanitized_job['banner_photo_url'],
                        sanitized_job['ceo_name'], sanitized_job['ceo_photo_url'],
                        sanitized_job['compensation_interval'], sanitized_job['salary_source'],
                        sanitized_job['company_rating'], sanitized_job['skills'], sanitized_job['experience_range']
                    ))
                    
                    if cursor.rowcount > 0:
                        inserted_count += 1
                        self.logger.debug(f"✅ Inserted: {sanitized_job.get('title', 'Unknown')} at {sanitized_job.get('company_name', 'Unknown')}")
                    else:
                        self.logger.debug(f"⏭️  Duplicate skipped: {sanitized_job.get('title', 'Unknown')} at {sanitized_job.get('company_name', 'Unknown')}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Error inserting job {job_data.get('title', 'Unknown')}: {e}")
                    continue
            
            # Commit batch and free memory
            conn.commit()
            gc.collect()
        
        conn.close()
        
        self.logger.info(f"✅ Database insertion complete:")
        self.logger.info(f"   📈 New jobs inserted: {inserted_count}")
        self.logger.info(f"   🚫 Jobs outside SEA skipped: {skipped_count}")
        self.logger.info(f"   ⏭️  Duplicates skipped: {len(jobs_data) - inserted_count - skipped_count}")
        
        return inserted_count
    
    def search_jobs(self, filters: Dict[str, Any] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int]:
        """
        Search jobs with filters and pagination.
        
        Args:
            filters: Search filters
            page: Page number (1-based)
            per_page: Results per page
            
        Returns:
            Tuple of (jobs_list, total_count)
        """
        if filters is None:
            filters = {}
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if filters.get('title'):
            where_conditions.append("title LIKE ?")
            params.append(f"%{filters['title']}%")
        
        if filters.get('company'):
            where_conditions.append("company_name LIKE ?")
            params.append(f"%{filters['company']}%")
        
        if filters.get('location'):
            where_conditions.append("location LIKE ?")
            params.append(f"%{filters['location']}%")
        
        if filters.get('country'):
            where_conditions.append("location LIKE ?")
            params.append(f"%{filters['country']}%")
        
        if filters.get('job_type'):
            where_conditions.append("job_type = ?")
            params.append(filters['job_type'])
        
        if filters.get('site'):
            where_conditions.append("site = ?")
            params.append(filters['site'])
        
        if filters.get('is_remote'):
            where_conditions.append("is_remote = ?")
            params.append(1 if str(filters['is_remote']).lower() == 'true' else 0)
        
        if filters.get('min_salary'):
            where_conditions.append("(min_amount >= ? OR max_amount >= ?)")
            params.extend([float(filters['min_salary']), float(filters['min_salary'])])
        
        if filters.get('max_salary'):
            where_conditions.append("(min_amount <= ? OR max_amount <= ?)")
            params.extend([float(filters['max_salary']), float(filters['max_salary'])])
        
        if filters.get('days_old'):
            cutoff_date = datetime.now() - timedelta(days=int(filters['days_old']))
            where_conditions.append("scraped_at >= ?")
            params.append(cutoff_date.strftime('%Y-%m-%d %H:%M:%S'))
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Build ORDER BY clause
        sort_by = filters.get('sort_by', 'scraped_at')
        sort_order = filters.get('sort_order', 'desc').upper()
        
        # Validate sort fields
        valid_sort_fields = ['title', 'company_name', 'location', 'min_amount', 'max_amount', 'date_posted', 'scraped_at']
        if sort_by not in valid_sort_fields:
            sort_by = 'scraped_at'
        
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'DESC'
        
        order_clause = f"ORDER BY {sort_by} {sort_order}"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM jobs WHERE {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = f"""
            SELECT * FROM jobs 
            WHERE {where_clause} 
            {order_clause}
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, params + [per_page, offset])
        
        jobs = []
        for row in cursor.fetchall():
            job_dict = dict(row)
            jobs.append(job_dict)
        
        conn.close()
        return jobs, total_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        stats['total_jobs'] = cursor.fetchone()[0]
        
        # Jobs by country
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN location LIKE '%Singapore%' THEN 'Singapore'
                    WHEN location LIKE '%Indonesia%' OR location LIKE '%Jakarta%' THEN 'Indonesia'
                    WHEN location LIKE '%Malaysia%' OR location LIKE '%Kuala Lumpur%' THEN 'Malaysia'
                    WHEN location LIKE '%Thailand%' OR location LIKE '%Bangkok%' THEN 'Thailand'
                    WHEN location LIKE '%Vietnam%' OR location LIKE '%Ho Chi Minh%' OR location LIKE '%Hanoi%' THEN 'Vietnam'
                    ELSE 'Other'
                END as country,
                COUNT(*) as count
            FROM jobs 
            GROUP BY country 
            ORDER BY count DESC
        """)
        stats['jobs_by_country'] = [{'country': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Jobs by site
        cursor.execute("SELECT site, COUNT(*) FROM jobs GROUP BY site ORDER BY COUNT(*) DESC")
        stats['jobs_by_site'] = [{'site': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Remote jobs percentage
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_remote = 1")
        remote_count = cursor.fetchone()[0]
        stats['remote_percentage'] = (remote_count / stats['total_jobs'] * 100) if stats['total_jobs'] > 0 else 0
        
        # Salary statistics
        cursor.execute("""
            SELECT 
                AVG(min_amount) as avg_min,
                AVG(max_amount) as avg_max,
                MIN(min_amount) as min_salary,
                MAX(max_amount) as max_salary,
                COUNT(*) as jobs_with_salary
            FROM jobs 
            WHERE min_amount IS NOT NULL OR max_amount IS NOT NULL
        """)
        salary_row = cursor.fetchone()
        if salary_row and salary_row[4] > 0:
            stats['salary_stats'] = {
                'avg_min_salary': round(salary_row[0] or 0, 2),
                'avg_max_salary': round(salary_row[1] or 0, 2),
                'min_salary': salary_row[2],
                'max_salary': salary_row[3],
                'jobs_with_salary': salary_row[4],
                'percentage_with_salary': round(salary_row[4] / stats['total_jobs'] * 100, 1) if stats['total_jobs'] > 0 else 0
            }
        else:
            stats['salary_stats'] = {
                'avg_min_salary': 0,
                'avg_max_salary': 0,
                'min_salary': 0,
                'max_salary': 0,
                'jobs_with_salary': 0,
                'percentage_with_salary': 0
            }
        
        conn.close()
        return stats
    
    def cleanup_old_jobs(self, days: int = 14) -> int:
        """
        Remove jobs older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of jobs deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cursor.execute(
            "DELETE FROM jobs WHERE scraped_at < ?",
            (cutoff_date.strftime('%Y-%m-%d %H:%M:%S'),)
        )
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        self.logger.info(f"🧹 Cleaned up {deleted_count} old jobs (older than {days} days)")
        return deleted_count
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get available filter options."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        options = {}
        
        # Get unique companies
        cursor.execute("SELECT DISTINCT company_name FROM jobs WHERE company_name IS NOT NULL ORDER BY company_name LIMIT 100")
        options['companies'] = [row[0] for row in cursor.fetchall()]
        
        # Get unique locations
        cursor.execute("SELECT DISTINCT location FROM jobs WHERE location IS NOT NULL ORDER BY location LIMIT 50")
        options['locations'] = [row[0] for row in cursor.fetchall()]
        
        # Get unique job types
        cursor.execute("SELECT DISTINCT job_type FROM jobs WHERE job_type IS NOT NULL ORDER BY job_type")
        options['job_types'] = [row[0] for row in cursor.fetchall()]
        
        # Get unique sites
        cursor.execute("SELECT DISTINCT site FROM jobs ORDER BY site")
        options['sites'] = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return options 