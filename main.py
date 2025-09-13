#!/usr/bin/env python3
"""
Systematic Review Data Extraction Tool
======================================

This tool automates the data extraction process for systematic reviews by:
1. Reading articles from Google Sheets
2. Fetching full-text articles using DOI/PMIDs
3. Extracting structured data using DSPy LLM agents
4. Populating the Google Sheets with extracted data
5. Logging progress and results

Author: GitHub Copilot
Date: September 2025
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import dspy
from dotenv import load_dotenv

from src.config import Config
from src.sheets_client import SheetsClient
from src.article_fetcher import ArticleFetcher
from src.data_extractor import DataExtractor
from src.progress_tracker import ProgressTracker
from src.rate_limiter import RateLimiter

# Load environment variables
load_dotenv()

def setup_logging():
    """Setup logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"systematic_review_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def configure_dspy():
    """Configure DSPy with Azure OpenAI."""
    try:
        # Configure Azure OpenAI LM with required settings for reasoning models
        lm = dspy.LM(
            model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
            api_key=os.getenv('AZURE_OPENAI_KEY'),
            api_base=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            temperature=1.0,  # Required for reasoning models
            max_tokens=16000  # Required minimum for reasoning models
        )
        dspy.configure(lm=lm)
        
        logger = logging.getLogger(__name__)
        logger.info("DSPy configured successfully with Azure OpenAI")
        return True
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to configure DSPy: {e}")
        return False

async def main():
    """Main execution function."""
    logger = setup_logging()
    logger.info("Starting Systematic Review Data Extraction Tool")
    
    # Configure DSPy
    if not configure_dspy():
        logger.error("Failed to configure DSPy. Exiting.")
        return
    
    try:
        # Initialize components
        config = Config()
        sheets_client = SheetsClient(config.sheets_config)
        article_fetcher = ArticleFetcher(config.fetcher_config)
        data_extractor = DataExtractor(config.extraction_config)
        progress_tracker = ProgressTracker(config.tracking_config)
        rate_limiter = RateLimiter(config.rate_limit_config)
        
        # Get articles from Google Sheets
        logger.info("Fetching articles from Google Sheets...")
        articles = await sheets_client.get_articles()
        logger.info(f"Found {len(articles)} articles to process")
        
        # Process each article
        for i, article in enumerate(articles, 1):
            logger.info(f"Processing article {i}/{len(articles)}: {article.get('title', 'Unknown')}")
            
            # Check if already processed
            if progress_tracker.is_processed(article['id']):
                logger.info(f"Article {article['id']} already processed, skipping")
                continue
            
            # Rate limiting
            await rate_limiter.wait()
            
            try:
                # Fetch full text
                full_text = await article_fetcher.fetch_article(article)
                
                if not full_text:
                    logger.warning(f"Could not fetch full text for article {article['id']}")
                    progress_tracker.log_failure(article['id'], "Failed to fetch full text")
                    continue
                
                # Extract data
                extracted_data = await data_extractor.extract_all_data(full_text, article)
                
                # Update Google Sheets
                await sheets_client.update_extracted_data(article['id'], extracted_data)
                
                # Track progress
                progress_tracker.log_success(article['id'], extracted_data)
                
                logger.info(f"Successfully processed article {article['id']}")
                
            except Exception as e:
                logger.error(f"Error processing article {article['id']}: {e}")
                progress_tracker.log_failure(article['id'], str(e))
                continue
        
        logger.info("Data extraction completed successfully")
        
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
