#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.sheets_client import SheetsClient

async def check_articles_structure():
    config = Config()
    client = SheetsClient(config.sheets_config)
    await client.test_connection()
    
    # Get first few rows of articles sheet
    result = client.service.spreadsheets().values().get(
        spreadsheetId=config.sheets_config.spreadsheet_id,
        range='articles!A1:Z3'  # First 3 rows
    ).execute()
    
    values = result.get('values', [])
    print('Articles sheet structure:')
    for i, row in enumerate(values, 1):
        print(f'Row {i}: {row[:5]}...')  # Show first 5 columns

asyncio.run(check_articles_structure())
