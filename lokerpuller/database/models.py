"""
Database models for LokerPuller.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Job:
    """Job posting model."""
    
    # Required fields
    site: str
    job_url: str
    title: str
    
    # Optional fields
    id: Optional[int] = None
    job_url_direct: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    date_posted: Optional[str] = None
    interval: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    is_remote: bool = False
    job_level: Optional[str] = None
    job_function: Optional[str] = None
    company_industry: Optional[str] = None
    listing_type: Optional[str] = None
    emails: Optional[str] = None
    description: Optional[str] = None
    company_url: Optional[str] = None
    company_url_direct: Optional[str] = None
    company_addresses: Optional[str] = None
    company_num_employees: Optional[str] = None
    company_revenue: Optional[str] = None
    company_description: Optional[str] = None
    logo_photo_url: Optional[str] = None
    banner_photo_url: Optional[str] = None
    ceo_name: Optional[str] = None
    ceo_photo_url: Optional[str] = None
    compensation_interval: Optional[str] = None
    salary_source: Optional[str] = None
    company_rating: Optional[float] = None
    skills: Optional[str] = None
    experience_range: Optional[str] = None
    scraped_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> "Job":
        """Create Job instance from dictionary."""
        # Map common field variations
        field_mapping = {
            'company': 'company_name',
            'company_logo': 'logo_photo_url',
        }
        
        # Apply field mapping
        mapped_data = {}
        for key, value in data.items():
            mapped_key = field_mapping.get(key, key)
            mapped_data[mapped_key] = value
        
        # Filter only valid fields
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in mapped_data.items() if k in valid_fields}
        
        return cls(**filtered_data)
    
    def to_dict(self) -> dict:
        """Convert Job instance to dictionary."""
        result = {}
        for field_name, field_def in self.__dataclass_fields__.items():
            value = getattr(self, field_name)
            if value is not None:
                if isinstance(value, datetime):
                    result[field_name] = value.isoformat()
                else:
                    result[field_name] = value
        return result
    
    def get_salary_range(self) -> Optional[str]:
        """Get formatted salary range string."""
        if self.min_amount is None and self.max_amount is None:
            return None
        
        currency = self.currency or "USD"
        
        if self.min_amount is not None and self.max_amount is not None:
            return f"{currency} {self.min_amount:,.0f} - {self.max_amount:,.0f}"
        elif self.min_amount is not None:
            return f"{currency} {self.min_amount:,.0f}+"
        elif self.max_amount is not None:
            return f"Up to {currency} {self.max_amount:,.0f}"
        
        return None
    
    def is_valid(self) -> bool:
        """Check if job has required fields."""
        return bool(self.site and self.job_url and self.title) 