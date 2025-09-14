#!/usr/bin/env python3
"""
Check actual headers in Google Sheets vs extracted data field names.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.sheets_client import SheetsClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CheckHeaders')

async def check_headers():
    """Check the actual headers in all sheets."""
    
    config = Config()
    sheets_client = SheetsClient(config.sheets_config)
    
    # Test connection
    if not await sheets_client.test_connection():
        logger.error("Connection failed")
        return
    
    # Check headers for each sheet
    sheet_names = [
        'Study Characteristics',
        'Population Characteristics',
        'Interventions & Comparators',
        'Primary Outcomes (SSI Epidemiology & AMR)',
        'Secondary Outcomes (Clinical & Economic Impact)',
        'Drivers, Innovations & Policy Context'
    ]
    
    for sheet_name in sheet_names:
        logger.info(f"\n=== {sheet_name} ===")
        headers = await sheets_client.get_sheet_headers(sheet_name)
        logger.info(f"Headers ({len(headers)}): {headers}")
        
        # Show the column letters too
        for i, header in enumerate(headers):
            column_letter = chr(ord('A') + i)
            logger.info(f"  {column_letter}: {header}")

if __name__ == "__main__":
    asyncio.run(check_headers())
