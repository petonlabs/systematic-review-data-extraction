"""
Configuration module for systematic review data extraction.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class SheetsConfig:
    """Configuration for Google Sheets API."""
    spreadsheet_id: str
    credentials_file: str = "credentials.json"
    token_file: str = "token.json"
    scopes: list = None
    
    def __post_init__(self):
        if self.scopes is None:
            self.scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.readonly'
            ]


@dataclass 
class FetcherConfig:
    """Configuration for article fetching."""
    max_retries: int = 3
    timeout: int = 30
    use_proxies: bool = False
    proxy_list: list = None
    
    # API configurations
    crossref_email: str = None
    unpaywall_email: str = None
    
    def __post_init__(self):
        if self.proxy_list is None:
            self.proxy_list = []


@dataclass
class ExtractionConfig:
    """Configuration for data extraction using DSPy."""
    max_tokens: int = 16000  # Required minimum for reasoning models
    temperature: float = 1.0  # Required for reasoning models
    chunk_size: int = 12000  # Context window management - reduced to leave room for prompts
    overlap: int = 500
    timeout: int = 60  # Timeout in seconds for requests
    
    # DSPy specific settings
    cache_results: bool = True
    retry_on_failure: int = 2


@dataclass
class TrackingConfig:
    """Configuration for progress tracking."""
    database_file: str = "progress.db"
    backup_frequency: int = 10  # Backup every N processed articles
    log_format: str = "csv"  # csv, json, or sqlite


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    sheets_requests_per_minute: int = 60
    api_requests_per_minute: int = 30
    azure_requests_per_minute: int = 60
    
    # Delays between requests (seconds)
    base_delay: float = 1.0
    exponential_backoff: bool = True


@dataclass
class PdfConfig:
    """Configuration for PDF processing."""
    max_text_length: int = 50000  # Maximum characters to extract from PDF
    page_chunk_size: int = 10  # Process pages in chunks
    min_page_text_length: int = 50  # Minimum text length per page
    timeout: int = 120  # Timeout for PDF processing operations
    
    # Memory management
    max_memory_mb: int = 512  # Maximum memory usage for PDF processing
    use_temp_files: bool = True  # Use temporary files for large PDFs


@dataclass
class R2Config:
    """Configuration for Cloudflare R2 storage."""
    endpoint_url: str = None
    access_key_id: str = None
    secret_access_key: str = None
    bucket_name: str = None
    region: str = "auto"  # Usually 'auto' for Cloudflare R2
    
    # Storage settings
    pdf_prefix: str = "pdfs/"  # Prefix for PDF files in bucket
    max_file_size_mb: int = 100  # Maximum PDF file size
    retention_days: int = 365  # How long to keep PDFs
    
    def __post_init__(self):
        # Load from environment variables if not provided
        self.endpoint_url = self.endpoint_url or os.getenv('R2_ENDPOINT_URL')
        self.access_key_id = self.access_key_id or os.getenv('R2_ACCESS_KEY_ID')
        self.secret_access_key = self.secret_access_key or os.getenv('R2_SECRET_ACCESS_KEY')
        self.bucket_name = self.bucket_name or os.getenv('R2_BUCKET_NAME')


class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.sheets_config = SheetsConfig(
            spreadsheet_id="1ki0z_9QHBg4uUCe4HVN5Rx7Tp6kzeIrJCGsnQTZku_Q"
        )
        
        self.fetcher_config = FetcherConfig(
            crossref_email=os.getenv('CROSSREF_EMAIL', 'researcher@university.edu'),
            unpaywall_email=os.getenv('UNPAYWALL_EMAIL', 'researcher@university.edu')
        )
        
        self.extraction_config = ExtractionConfig()
        self.tracking_config = TrackingConfig()
        self.rate_limit_config = RateLimitConfig()
        self.pdf_config = PdfConfig()
        self.r2_config = R2Config()
        
        # Azure OpenAI configuration (loaded from .env)
        self.azure_config = {
            'endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'key': os.getenv('AZURE_OPENAI_KEY'),
            'deployment': os.getenv('AZURE_OPENAI_DEPLOYMENT'),
            'api_version': os.getenv('AZURE_OPENAI_API_VERSION', '2023-12-01-preview')
        }
    
    def validate(self) -> bool:
        """Validate configuration."""
        required_azure_keys = ['endpoint', 'key', 'deployment']
        
        for key in required_azure_keys:
            if not self.azure_config.get(key):
                raise ValueError(f"Missing required Azure OpenAI configuration: {key}")
        
        if not self.sheets_config.spreadsheet_id:
            raise ValueError("Missing Google Sheets spreadsheet ID")
        
        return True
    
    def validate_r2_config(self) -> bool:
        """Validate Cloudflare R2 configuration."""
        required_r2_keys = ['endpoint_url', 'access_key_id', 'secret_access_key', 'bucket_name']
        
        for key in required_r2_keys:
            if not getattr(self.r2_config, key):
                return False
        
        return True
