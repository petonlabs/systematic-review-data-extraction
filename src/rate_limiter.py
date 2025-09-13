"""
Rate limiter for managing API calls and respecting service limits.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict
from collections import deque

from .config import RateLimitConfig


class RateLimiter:
    """Manage rate limiting for various APIs and services."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Track requests for different services
        self.request_timestamps = {
            'sheets': deque(),
            'api': deque(),  # General API requests (CrossRef, Unpaywall, etc.)
            'azure': deque(),  # Azure OpenAI requests
        }
        
        # Service limits (requests per minute)
        self.limits = {
            'sheets': config.sheets_requests_per_minute,
            'api': config.api_requests_per_minute,
            'azure': config.azure_requests_per_minute,
        }
        
        self.logger.info("Rate limiter initialized with limits: "
                        f"Sheets={self.limits['sheets']}/min, "
                        f"API={self.limits['api']}/min, "
                        f"Azure={self.limits['azure']}/min")
    
    async def wait_for_sheets(self):
        """Wait before making a Google Sheets API request."""
        await self._wait_for_service('sheets')
    
    async def wait_for_api(self):
        """Wait before making a general API request."""
        await self._wait_for_service('api')
    
    async def wait_for_azure(self):
        """Wait before making an Azure OpenAI request."""
        await self._wait_for_service('azure')
    
    async def wait(self):
        """General wait method (uses API limits by default)."""
        await self.wait_for_api()
    
    async def _wait_for_service(self, service: str):
        """Wait for a specific service based on its rate limits."""
        if service not in self.request_timestamps:
            self.logger.warning(f"Unknown service: {service}")
            return
        
        now = datetime.now()
        timestamps = self.request_timestamps[service]
        limit = self.limits[service]
        
        # Remove timestamps older than 1 minute
        one_minute_ago = now - timedelta(minutes=1)
        while timestamps and timestamps[0] < one_minute_ago:
            timestamps.popleft()
        
        # Check if we need to wait
        if len(timestamps) >= limit:
            # Calculate wait time until the oldest request is more than 1 minute old
            oldest_timestamp = timestamps[0]
            wait_until = oldest_timestamp + timedelta(minutes=1)
            wait_seconds = (wait_until - now).total_seconds()
            
            if wait_seconds > 0:
                self.logger.info(f"Rate limit reached for {service}, waiting {wait_seconds:.1f} seconds")
                await asyncio.sleep(wait_seconds)
        
        # Add base delay if configured
        if self.config.base_delay > 0:
            await asyncio.sleep(self.config.base_delay)
        
        # Record this request
        timestamps.append(now)
        
        self.logger.debug(f"Rate limiter: {service} requests in last minute: {len(timestamps)}/{limit}")
    
    async def exponential_backoff(self, attempt: int, max_delay: float = 60.0):
        """Apply exponential backoff for retries."""
        if not self.config.exponential_backoff:
            return
        
        delay = min(self.config.base_delay * (2 ** attempt), max_delay)
        self.logger.info(f"Exponential backoff: waiting {delay:.1f} seconds (attempt {attempt + 1})")
        await asyncio.sleep(delay)
    
    def get_status(self) -> Dict[str, Dict]:
        """Get current rate limiter status."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        status = {}
        
        for service in self.request_timestamps:
            timestamps = self.request_timestamps[service]
            
            # Count recent requests
            recent_requests = sum(1 for ts in timestamps if ts > one_minute_ago)
            
            status[service] = {
                'recent_requests': recent_requests,
                'limit': self.limits[service],
                'remaining': max(0, self.limits[service] - recent_requests),
                'reset_in_seconds': None
            }
            
            # Calculate when limit resets (when oldest request expires)
            if timestamps and recent_requests >= self.limits[service]:
                oldest_recent = min(ts for ts in timestamps if ts > one_minute_ago)
                reset_time = oldest_recent + timedelta(minutes=1)
                status[service]['reset_in_seconds'] = (reset_time - now).total_seconds()
        
        return status
    
    def reset_service(self, service: str):
        """Reset rate limit tracking for a specific service (for testing)."""
        if service in self.request_timestamps:
            self.request_timestamps[service].clear()
            self.logger.info(f"Reset rate limit tracking for {service}")
        else:
            self.logger.warning(f"Unknown service: {service}")
    
    def reset_all(self):
        """Reset all rate limit tracking (for testing)."""
        for service in self.request_timestamps:
            self.request_timestamps[service].clear()
        self.logger.info("Reset all rate limit tracking")
