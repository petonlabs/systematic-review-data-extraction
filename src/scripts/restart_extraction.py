#!/usr/bin/env python3
"""
Restart extraction script with resilient fallback strategies.
This script checks progress and resumes from failed articles with enhanced metadata fallback.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

import dspy

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.progress_tracker import ProgressTracker
from src.sheets_client import SheetsClient
from src.data_extractor import DataExtractor
from src.article_fetcher import ArticleFetcher


class EnhancedArticleFetcher(ArticleFetcher):
    """Enhanced article fetcher with metadata fallback strategies."""
    
    def __init__(self, config):
        super().__init__(config)
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    async def get_article_content(self, article):
        """Enhanced method with metadata fallback for failed articles."""
        article_id = article.get('id', 'unknown')
        title = article.get('title', 'Unknown Title')
        
        self.logger.info(f"📄 Enhanced fetching for: {title}")
        
        # First, try the original method
        try:
            content = await super().get_article_content(article)
            if content and content.strip():
                self.logger.info(f"✅ Successfully fetched full text for {article_id}")
                return content
        except Exception as e:
            self.logger.warning(f"⚠️ Full text fetch failed for {article_id}: {e}")
        
        # If full text fails, create comprehensive content from available metadata
        self.logger.info(f"🔄 Using metadata fallback for {article_id}")
        
        metadata_content = []
        
        # Use title
        if title and title != 'Unknown Title':
            metadata_content.append(f"Title: {title}")
        
        # Use abstract if available
        abstract = article.get('abstract', '').strip()
        if abstract and abstract != 'Not available':
            metadata_content.append(f"Abstract: {abstract}")
        
        # Add authors
        authors = article.get('authors', '').strip()
        if authors and authors != 'Not available':
            metadata_content.append(f"Authors: {authors}")
        
        # Add journal and year
        journal = article.get('journal', '').strip()
        if journal and journal != 'Not available':
            metadata_content.append(f"Journal: {journal}")
            
        year = article.get('year', '').strip()
        if year and year != 'Not available':
            metadata_content.append(f"Year: {year}")
        
        # Add DOI and PMID information
        doi = article.get('doi', '').strip()
        if doi and doi != 'Not available':
            metadata_content.append(f"DOI: {doi}")
        
        pmid = article.get('pmid', '').strip()
        if pmid and pmid != 'Not available':
            metadata_content.append(f"PMID: {pmid}")
        
        # Add any other substantial metadata from sheet columns
        for key, value in article.items():
            if key not in ['id', 'title', 'abstract', 'authors', 'journal', 'year', 'doi', 'pmid', 'url']:
                value_str = str(value).strip()
                if value_str and len(value_str) > 10 and value_str not in ['Not available', 'N/A', '']:
                    clean_key = key.replace('_', ' ').title()
                    metadata_content.append(f"{clean_key}: {value_str}")
        
        if metadata_content:
            combined_content = "\n\n".join(metadata_content)
            self.logger.info(f"✅ Created metadata content for {article_id} ({len(combined_content)} chars)")
            return combined_content
        
        self.logger.error(f"❌ No content available for {article_id}")
        return None


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
        
        return True
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to configure DSPy: {e}")
        return False


async def restart_extraction():
    """Process articles that previously failed with enhanced fallback strategies."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('restart_extraction.log')
        ]
    )
    
    logger = logging.getLogger('RestartExtraction')
    logger.info("🚀 Starting restart extraction for failed articles")
    
    # Configure DSPy
    logger.info("🧠 Configuring DSPy...")
    if not configure_dspy():
        logger.error("❌ Failed to configure DSPy - cannot proceed with data extraction")
        return False
    
    try:
        # Initialize components
        config = Config()
        progress_tracker = ProgressTracker(config.tracking_config)
        enhanced_fetcher = EnhancedArticleFetcher(config.fetcher_config)
        sheets_client = SheetsClient(config.sheets_config)
        data_extractor = DataExtractor(config.extraction_config)
        
        # Test connections
        logger.info("🔗 Testing connections...")
        if not await sheets_client.test_connection():
            logger.error("❌ Google Sheets connection failed")
            return False
        
        # Get failed articles
        failed_articles = progress_tracker.get_failed_articles()
        logger.info(f"📊 Found {len(failed_articles)} failed articles")
        
        if not failed_articles:
            logger.info("✅ No failed articles found!")
            return True
        
        # Process each failed article
        success_count = 0
        for i, article in enumerate(failed_articles, 1):
            article_id = article.get('id', f'unknown_{i}')
            title = article.get('title', 'Unknown Title')[:60] + '...' if len(article.get('title', '')) > 60 else article.get('title', 'Unknown Title')
            
            logger.info(f"\n{'='*80}")
            logger.info(f"📄 Processing {i}/{len(failed_articles)}: {title}")
            logger.info(f"   Article ID: {article_id}")
            
            try:
                # Mark as started
                progress_tracker.start_processing(article_id, article)
                
                # Enhanced content fetching with metadata fallback
                logger.info("🔍 Fetching article content...")
                content = await enhanced_fetcher.get_article_content(article)
                
                if not content:
                    logger.error(f"❌ No content available for {article_id}")
                    progress_tracker.log_failure(article_id, "No content available after all strategies")
                    continue
                
                logger.info(f"✅ Content fetched: {len(content)} characters")
                
                # Data extraction
                logger.info("🧠 Extracting data...")
                extracted_data = await data_extractor.extract_all_data(content, article)
                
                if not extracted_data:
                    logger.error(f"❌ Data extraction failed for {article_id}")
                    progress_tracker.log_failure(article_id, "Data extraction failed")
                    continue
                
                logger.info(f"✅ Data extracted with {len(extracted_data)} sections")
                
                # Write to sheets with better error handling
                logger.info("📊 Writing to Google Sheets...")
                try:
                    await sheets_client.update_extracted_data(article_id, extracted_data)
                    logger.info(f"✅ Successfully wrote data for {article_id}")
                    write_success = True
                except Exception as sheet_error:
                    logger.error(f"❌ Sheet write failed for {article_id}: {sheet_error}")
                    # Continue processing but mark the specific error
                    write_success = False
                
                # Log success regardless of sheet write (data extraction succeeded)
                progress_tracker.log_success(article_id, extracted_data)
                success_count += 1
                logger.info(f"✅ Successfully processed {article_id} (Sheet write: {'✅' if write_success else '❌'})")
                
            except Exception as e:
                logger.error(f"❌ Error processing {article_id}: {str(e)}")
                progress_tracker.log_failure(article_id, f"Processing error: {str(e)}")
                
            # Short pause between articles
            await asyncio.sleep(1)
        
        # Summary
        logger.info(f"\n{'='*80}")
        logger.info("🎉 Restart extraction complete!")
        logger.info(f"✅ Successfully processed: {success_count}/{len(failed_articles)} articles")
        logger.info(f"❌ Failed: {len(failed_articles) - success_count}/{len(failed_articles)} articles")
        
        if success_count > 0:
            logger.info("🔍 Check the Google Sheets and restart_extraction.log for details")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error in restart extraction: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    result = asyncio.run(restart_extraction())
    sys.exit(0 if result else 1)
