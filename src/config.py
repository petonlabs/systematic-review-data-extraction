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
