#!/usr/bin/env python3
"""
Enhanced systematic review data extraction tool with PDF-based and web-based extraction methods.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from pathlib import Path

import dspy
from dotenv import load_dotenv

from src.config import Config
from src.sheets_client import SheetsClient
from src.enhanced_article_fetcher import EnhancedArticleFetcher
from src.data_extractor import DataExtractor
from src.progress_tracker import ProgressTracker
from src.rate_limiter import RateLimiter
from src.extraction_mode_manager import ExtractionModeManager, ExtractionMethod

# Load environment variables
load_dotenv()


def setup_logging():
    """Setup logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"enhanced_systematic_review_{timestamp}.log"
    
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


async def initialize_components(config: Config, extraction_method: ExtractionMethod) -> tuple:
    """Initialize all required components."""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize sheets client
        sheets_client = SheetsClient(config.sheets_config)
        
        # Initialize enhanced article fetcher
        article_fetcher = EnhancedArticleFetcher(config, extraction_method)
        
        # Make sure the session is created for the base fetcher functionality
        import aiohttp
        if not article_fetcher.session:
            article_fetcher.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=config.fetcher_config.timeout),
                headers=article_fetcher.headers
            )
        
        # Initialize data extractor
        data_extractor = DataExtractor(config.extraction_config)
        
        # Initialize progress tracker
        progress_tracker = ProgressTracker(config.tracking_config)
        
        # Initialize rate limiter
        rate_limiter = RateLimiter(config.rate_limit_config)
        
        logger.info("All components initialized successfully")
        return sheets_client, article_fetcher, data_extractor, progress_tracker, rate_limiter
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


async def process_articles(
    articles,
    sheets_client,
    article_fetcher,
    data_extractor,
    progress_tracker,
    rate_limiter,
    extraction_method: ExtractionMethod,
    mode_manager: ExtractionModeManager
):
    """Process articles using the selected extraction method."""
    logger = logging.getLogger(__name__)
    
    success_count = 0
    error_count = 0
    total_articles = len(articles)
    
    logger.info(f"Starting processing of {total_articles} articles using {extraction_method.value} method")
    
    for i, article in enumerate(articles, 1):
        article_id = article.get('id', f"row_{article.get('row_number', i)}")
        title = article.get('title', 'Unknown Title')[:50] + "..."
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing article {i}/{total_articles}: {title}")
        logger.info(f"Article ID: {article_id}")
        logger.info(f"Method: {extraction_method.value}")
        logger.info(f"{'='*80}")
        
        # Check if already processed
        if progress_tracker.is_processed(article_id):
            logger.info(f"Article {article_id} already processed, skipping")
            continue
        
        # Rate limiting
        await rate_limiter.wait()
        
        try:
            progress_tracker.start_processing(article_id, article)
            
            # Fetch article content using enhanced fetcher
            logger.info("🔍 Fetching article content...")
            fetch_result = await article_fetcher.fetch_article(article)
            
            if not fetch_result:
                logger.warning("❌ No content found for article")
                progress_tracker.log_failure(article_id, "No content found")
                error_count += 1
                continue
            
            # Handle different return types based on extraction method
            if extraction_method == ExtractionMethod.PDF_BASED and isinstance(fetch_result, tuple):
                full_text, metadata = fetch_result
                article_metadata = metadata
            else:
                full_text = fetch_result
                article_metadata = article
            
            if not full_text or len(full_text.strip()) < 100:
                logger.warning("❌ Insufficient content extracted")
                progress_tracker.log_failure(article_id, "Insufficient content")
                error_count += 1
                continue
            
            logger.info(f"✅ Fetched {len(full_text)} characters of content")
            if extraction_method == ExtractionMethod.PDF_BASED and 'pdf_stored' in article_metadata:
                logger.info("✅ PDF stored in Cloudflare R2")
            
            # Extract data using DSPy
            logger.info("🤖 Extracting structured data...")
            extracted_data = await data_extractor.extract_all_data(full_text, article_metadata)
            
            if not extracted_data:
                logger.warning("❌ No structured data extracted")
                progress_tracker.log_failure(article_id, "No structured data extracted")
                error_count += 1
                continue
            
            logger.info(f"✅ Extracted {len(extracted_data)} data categories")
            
            # Update Google Sheets
            logger.info("📊 Updating Google Sheets...")
            await sheets_client.update_extracted_data(article_id, extracted_data)
            
            # Log success
            progress_tracker.log_success(article_id, extracted_data)
            success_count += 1
            
            logger.info(f"🎉 Successfully processed article {i}/{total_articles}")
            
            # Update progress in mode manager
            mode_manager.update_progress(
                total_processed=success_count + error_count,
                successful=success_count,
                failed=error_count,
                resume_from=article_id
            )
            
        except Exception as e:
            logger.error(f"❌ Error processing article {article_id}: {e}")
            progress_tracker.log_failure(article_id, str(e))
            error_count += 1
            continue
        
        # Show progress
        progress_percent = (i / total_articles) * 100
        logger.info(f"📊 Progress: {progress_percent:.1f}% | ✅ {success_count} | ❌ {error_count}")
    
    # Final summary
    logger.info(f"\n🎉 Processing completed!")
    logger.info(f"📊 Final results: {success_count} successful, {error_count} errors")
    if success_count + error_count > 0:
        success_rate = (success_count / (success_count + error_count)) * 100
        logger.info(f"📈 Success rate: {success_rate:.1f}%")
    
    # Final progress update
    mode_manager.update_progress(
        total_processed=success_count + error_count,
        successful=success_count,
        failed=error_count,
        resume_from=None  # Processing complete
    )
    
    return success_count, error_count


async def main():
    """Main execution function."""
    logger = setup_logging()
    logger.info("🚀 Starting Enhanced Systematic Review Data Extraction Tool")
    
    # Configure DSPy
    if not configure_dspy():
        logger.error("Failed to configure DSPy. Exiting.")
        return False
    
    try:
        # Initialize configuration
        config = Config()
        config.validate()
        
        # Initialize extraction mode manager
        mode_manager = ExtractionModeManager(config)
        
        # Check if we have a saved extraction method
        current_method = mode_manager.get_current_method()
        
        if current_method:
            logger.info(f"Found existing extraction method: {current_method.value}")
            
            # Ask if user wants to continue with the same method
            try:
                continue_choice = input(f"Continue with {current_method.value} method? (Y/n): ").strip().lower()
                if continue_choice in ['n', 'no']:
                    current_method = mode_manager.choose_method_interactively()
                    if not current_method:
                        logger.info("No method selected, exiting.")
                        return False
            except KeyboardInterrupt:
                logger.info("Operation cancelled by user.")
                return False
        else:
            logger.info("No previous extraction method found, selecting method...")
            current_method = mode_manager.choose_method_interactively()
            if not current_method:
                logger.info("No method selected, exiting.")
                return False
        
        # Validate method availability
        if current_method == ExtractionMethod.PDF_BASED:
            if not mode_manager.is_pdf_method_available():
                logger.error("PDF-based method is not available due to missing dependencies or configuration")
                logger.info("Please install required packages or configure Cloudflare R2")
                return False
        
        logger.info(f"Using extraction method: {current_method.value}")
        
        # Initialize components with selected method
        components = await initialize_components(config, current_method)
        sheets_client, article_fetcher, data_extractor, progress_tracker, rate_limiter = components
        
        # Test connections
        logger.info("🔧 Testing connections...")
        if not await sheets_client.test_connection():
            logger.error("❌ Google Sheets connection failed")
            return False
        logger.info("✅ Google Sheets connection successful")
        
        # Test R2 connection if using PDF method
        if current_method == ExtractionMethod.PDF_BASED and article_fetcher.r2_storage:
            if await article_fetcher.r2_storage.test_connection():
                logger.info("✅ Cloudflare R2 connection successful")
            else:
                logger.warning("⚠️ Cloudflare R2 connection failed - PDFs will be processed locally only")
        
        # Get articles from Google Sheets
        logger.info("📊 Fetching articles from Google Sheets...")
        articles = await sheets_client.get_articles()
        logger.info(f"Found {len(articles)} articles to process")
        
        if not articles:
            logger.warning("No articles found in Google Sheets")
            return True
        
        # Show progress summary
        progress_summary = mode_manager.get_progress_summary()
        logger.info(f"Previous progress: {progress_summary}")
        
        # Process articles
        success_count, error_count = await process_articles(
            articles,
            sheets_client,
            article_fetcher,
            data_extractor,
            progress_tracker,
            rate_limiter,
            current_method,
            mode_manager
        )
        
        logger.info("Data extraction completed successfully")
        return True
        
    except KeyboardInterrupt:
        logger.info("\n⏸️ Extraction paused by user")
        logger.info("Progress has been saved. Run this script again to resume.")
        return True
        
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        raise


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Extraction interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)