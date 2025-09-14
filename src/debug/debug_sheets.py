#!/usr/bin/env python3
"""
Debug script to investigate Google Sheets writing issue.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.sheets_client import SheetsClient
from src.progress_tracker import ProgressTracker

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('DebugSheets')

async def debug_sheets_writing():
    """Debug the sheets writing process."""
    
    config = Config()
    sheets_client = SheetsClient(config.sheets_config)
    progress_tracker = ProgressTracker(config.tracking_config)
    
    # Test connection
    logger.info("Testing Google Sheets connection...")
    if not await sheets_client.test_connection():
        logger.error("Connection failed")
        return
    
    # Get some sample data from extracted results
    logger.info("Getting processed articles...")
    processed = progress_tracker.get_processed_articles()
    logger.info(f"Found {len(processed)} processed articles")
    
    if not processed:
        logger.info("No processed articles found")
        return
    
    # Get the database connection to examine extracted data
    import sqlite3
    db_path = config.tracking_config.database_file
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get extracted data for the first few articles
    cursor.execute("""
        SELECT DISTINCT article_id 
        FROM extraction_data 
        LIMIT 3
    """)
    
    article_ids = [row[0] for row in cursor.fetchall()]
    logger.info(f"Found {len(article_ids)} articles with extracted data")
    
    for article_id in article_ids:
        logger.info(f"\n=== Article {article_id} ===")
        
        # Get all extracted data for this article
        cursor.execute("""
            SELECT category, field_name, field_value 
            FROM extraction_data 
            WHERE article_id = ?
        """, (article_id,))
        
        extractions = cursor.fetchall()
        
        # Rebuild the extracted_data structure
        extracted_data = {}
        for category, field_name, field_value in extractions:
            if category not in extracted_data:
                extracted_data[category] = {}
            extracted_data[category][field_name] = field_value
        
        logger.info(f"Extracted data keys: {list(extracted_data.keys())}")
        
        for sheet_key, data in extracted_data.items():
            logger.info(f"  {sheet_key}: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            if isinstance(data, dict) and data:
                logger.info(f"    Sample data: {list(data.items())[:2]}")
        
        # Try to get the original article data
        articles = await sheets_client.get_articles()
        article = None
        for a in articles:
            if a['id'] == article_id:
                article = a
                break
        
        if article:
            logger.info(f"Article row number: {article.get('row_number', 'unknown')}")
            
            # Test the update process
            logger.info("Testing sheets update...")
            try:
                result = await sheets_client.update_extracted_data(article_id, extracted_data)
                logger.info(f"Update result: {result}")
            except Exception as e:
                logger.error(f"Update failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning(f"Could not find article {article_id} in sheets")
        
        break  # Just test one article for now
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(debug_sheets_writing())
