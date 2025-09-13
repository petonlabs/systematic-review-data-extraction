#!/usr/bin/env python3
"""
Simple extraction runner that loads the data extractor directly.
"""

import asyncio
import sys
import logging
import importlib.util
from pathlib import Path

from src.config import Config
from src.sheets_client import SheetsClient
from src.article_fetcher import ArticleFetcher
from src.progress_tracker import ProgressTracker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/extraction.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def load_data_extractor():
    """Load DataExtractor class directly from file."""
    try:
        spec = importlib.util.spec_from_file_location("data_extractor", "src/data_extractor.py")
        de_module = importlib.util.module_from_spec(spec)
        
        # Execute the module
        spec.loader.exec_module(de_module)
        
        # Get the DataExtractor class
        if hasattr(de_module, 'DataExtractor'):
            return de_module.DataExtractor
        else:
            raise ImportError("DataExtractor class not found in module")
            
    except Exception as e:
        logger.error(f"Failed to load DataExtractor: {e}")
        raise

async def main():
    """Run the extraction process."""
    logger.info("🚀 Starting systematic review data extraction...")
    
    # Load configuration
    config = Config()
    
    # Load DataExtractor
    logger.info("📦 Loading data extractor...")
    DataExtractor = load_data_extractor()
    
    # Initialize components
    logger.info("🔧 Initializing components...")
    sheets_client = SheetsClient(config.sheets_config)
    article_fetcher = ArticleFetcher(config.fetcher_config)
    data_extractor = DataExtractor(config.extraction_config)
    progress_tracker = ProgressTracker()
    
    # Authenticate
    logger.info("🔑 Authenticating with Google Sheets...")
    if not await sheets_client.authenticate():
        logger.error("❌ Failed to authenticate with Google Sheets")
        return False
    
    # Get articles
    logger.info("📊 Getting articles from Google Sheets...")
    articles = await sheets_client.get_articles()
    
    if not articles:
        logger.error("❌ No articles found in Google Sheets")
        return False
    
    logger.info(f"📚 Found {len(articles)} articles to process")
    
    # Check progress and resume
    progress = progress_tracker.get_summary()
    completed_articles = set()
    
    if progress['total_articles'] > 0:
        logger.info(f"📈 Resuming from previous run: {progress['completed_percentage']:.1f}% complete")
        # Get completed article IDs (this would need to be implemented in ProgressTracker)
        # For now, we'll start from the beginning
    
    # Process articles
    success_count = 0
    error_count = 0
    
    for i, article in enumerate(articles, 1):
        article_id = str(article.get('row_number', i))
        title = article.get('title', 'Unknown Title')[:50] + "..."
        
        logger.info(f"\n📄 Processing article {i}/{len(articles)}: {title}")
        logger.info(f"🆔 Article ID: {article_id}")
        
        try:
            # Skip if already completed
            if article_id in completed_articles:
                logger.info(f"⏭️  Article {article_id} already completed, skipping")
                continue
            
            progress_tracker.start_article(article_id)
            
            # Fetch article text
            logger.info("📥 Fetching article text...")
            text = await article_fetcher.fetch_article_text(article)
            
            if not text:
                logger.warning("❌ No text content found for article")
                progress_tracker.log_error(article_id, "No text content found", "fetch")
                error_count += 1
                continue
            
            logger.info(f"✅ Fetched {len(text)} characters of content")
            
            # Extract data
            logger.info("🤖 Extracting data...")
            extracted_data = await data_extractor.extract_all_data(text, article)
            
            if not extracted_data:
                logger.warning("❌ No data extracted")
                progress_tracker.log_error(article_id, "No data extracted", "extract")
                error_count += 1
                continue
            
            logger.info(f"✅ Extracted {len(extracted_data)} data categories")
            
            # Update sheets
            logger.info("📊 Updating Google Sheets...")
            if await sheets_client.update_extracted_data(article_id, extracted_data):
                progress_tracker.log_success(article_id, "extraction")
                success_count += 1
                logger.info("✅ Successfully updated Google Sheets")
            else:
                progress_tracker.log_error(article_id, "Failed to update sheets", "update")
                error_count += 1
                logger.warning("❌ Failed to update Google Sheets")
            
        except Exception as e:
            logger.error(f"❌ Error processing article {article_id}: {str(e)}")
            progress_tracker.log_error(article_id, str(e), "process")
            error_count += 1
            continue
        
        # Show progress
        progress_percent = (i / len(articles)) * 100
        logger.info(f"📊 Progress: {progress_percent:.1f}% ({i}/{len(articles)}) | ✅ {success_count} | ❌ {error_count}")
    
    # Final summary
    logger.info(f"\n🎉 Extraction completed!")
    logger.info(f"📊 Final results: {success_count} successful, {error_count} errors")
    logger.info(f"📈 Success rate: {(success_count/(success_count+error_count)*100):.1f}%")
    
    return True

if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Extraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)
