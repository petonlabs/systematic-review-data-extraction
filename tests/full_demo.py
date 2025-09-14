#!/usr/bin/env python3
"""
Complete demonstration of the systematic review data extraction system.
This processes actual articles from your Google Sheet and shows the full workflow.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import Config
from src.sheets_client import SheetsClient
from src.article_fetcher import ArticleFetcher
from src.data_extractor import DataExtractor
from src.progress_tracker import ProgressTracker
from src.rate_limiter import RateLimiter
import dspy
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def configure_dspy():
    """Configure DSPy with Azure OpenAI."""
    try:
        lm = dspy.LM(
            model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
            api_key=os.getenv('AZURE_OPENAI_KEY'),
            api_base=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            temperature=0.1,
            max_tokens=16000
        )
        dspy.configure(lm=lm)
        return True
    except Exception as e:
        print(f"❌ Failed to configure DSPy: {e}")
        return False

async def run_full_demo(max_articles=3, enable_sheets_update=False):
    """Run the complete data extraction demo."""
    
    print("🔬 SYSTEMATIC REVIEW DATA EXTRACTION - FULL DEMO")
    print("=" * 70)
    print(f"📊 Processing up to {max_articles} articles from your Google Sheet")
    print(f"🔄 Google Sheets updates: {'ENABLED' if enable_sheets_update else 'DISABLED (demo mode)'}")
    print("=" * 70)
    
    # Configure DSPy
    if not configure_dspy():
        return False
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        # Initialize all components
        print("\n⚙️  Initializing system components...")
        config = Config()
        sheets_client = SheetsClient(config.sheets_config)
        article_fetcher = ArticleFetcher(config.fetcher_config)
        data_extractor = DataExtractor(config.extraction_config)
        progress_tracker = ProgressTracker(config.tracking_config)
        rate_limiter = RateLimiter(config.rate_limit_config)
        print("✅ All components initialized")
        
        # Get articles from Google Sheets
        print(f"\n📋 Fetching articles from Google Sheets...")
        articles = await sheets_client.get_articles()
        
        if not articles:
            print("❌ No articles found in Google Sheets")
            return False
        
        print(f"✅ Found {len(articles)} articles with DOI/PMID")
        
        # Process articles
        processed_count = 0
        success_count = 0
        
        for i, article in enumerate(articles[:max_articles], 1):
            print(f"\n{'='*20} ARTICLE {i}/{min(max_articles, len(articles))} {'='*20}")
            
            title = article.get('title', 'Unknown Title')
            print(f"📄 Title: {title[:100]}{'...' if len(title) > 100 else ''}")
            print(f"🔗 DOI: {article.get('doi', 'N/A')}")
            print(f"🆔 PMID: {article.get('pmid', 'N/A')}")
            print(f"📅 Year: {article.get('publication_year', 'N/A')}")
            
            # Check if already processed
            if progress_tracker.is_processed(article['id']):
                print("✅ Already processed - skipping")
                continue
            
            processed_count += 1
            progress_tracker.start_processing(article['id'], article)
            
            try:
                # Rate limiting
                await rate_limiter.wait()
                
                # Fetch article content
                print("🔍 Fetching article content...")
                
                # For demo, use abstract if available, otherwise try to fetch
                if article.get('abstract_note'):
                    print("📝 Using abstract from Google Sheets")
                    article_text = f"""
                    Title: {article.get('title', '')}
                    Abstract: {article.get('abstract_note', '')}
                    Publication: {article.get('publication_title', '')}
                    Year: {article.get('publication_year', '')}
                    Keywords: {article.get('keywords', '')}
                    """
                else:
                    print("🌐 Attempting to fetch full text from web sources...")
                    async with article_fetcher:
                        article_text = await article_fetcher.fetch_article(article)
                    
                    if not article_text:
                        print("⚠️  Could not fetch article content")
                        progress_tracker.log_failure(article['id'], "Could not fetch content")
                        continue
                
                # Clean and prepare text
                if len(article_text.strip()) < 200:
                    print("⚠️  Insufficient content for extraction")
                    progress_tracker.log_failure(article['id'], "Insufficient content")
                    continue
                
                print(f"📊 Content length: {len(article_text)} characters")
                
                # Extract structured data
                print("🧠 Extracting structured data using DSPy LLM agents...")
                extracted_data = await data_extractor.extract_all_data(article_text, article)
                
                if not extracted_data:
                    print("❌ No data could be extracted")
                    progress_tracker.log_failure(article['id'], "No data extracted")
                    continue
                
                # Display results
                print(f"✅ Successfully extracted {len(extracted_data)} data categories:")
                
                for category, fields in extracted_data.items():
                    if fields:
                        print(f"\n  📋 {category.replace('_', ' ').title()} ({len(fields)} fields):")
                        for field_name, field_value in fields.items():
                            if field_value and field_value.strip():
                                display_value = field_value[:120] + "..." if len(field_value) > 120 else field_value
                                print(f"    • {field_name.replace('_', ' ').title()}: {display_value}")
                
                # Update Google Sheets if enabled
                if enable_sheets_update:
                    print("💾 Updating Google Sheets with extracted data...")
                    await sheets_client.update_extracted_data(article['id'], extracted_data)
                    print("✅ Google Sheets updated")
                else:
                    print("💾 (Demo mode: Not updating Google Sheets)")
                
                # Log success
                progress_tracker.log_success(article['id'], extracted_data)
                success_count += 1
                
                print("✅ Article processing completed successfully!")
                
            except Exception as e:
                print(f"❌ Error processing article: {e}")
                progress_tracker.log_failure(article['id'], str(e))
                continue
        
        # Final summary
        print(f"\n{'='*70}")
        print("📈 DEMO RESULTS SUMMARY")
        print(f"{'='*70}")
        
        summary = progress_tracker.get_progress_summary()
        print(f"Articles processed: {processed_count}")
        print(f"Successful extractions: {success_count}")
        print(f"Success rate: {(success_count/processed_count)*100 if processed_count > 0 else 0:.1f}%")
        
        # Export results
        if success_count > 0:
            print(f"\n💾 Exporting results...")
            try:
                progress_tracker.export_results("demo_results.csv", "csv")
                progress_tracker.export_results("demo_results.json", "json")
                print("✅ Results exported to demo_results.csv and demo_results.json")
            except Exception as e:
                print(f"⚠️  Export warning: {e}")
        
        print(f"\n🎉 Demo completed!")
        print(f"\n📋 Next Steps:")
        print(f"   • To process ALL {len(articles)} articles: python main.py")
        print(f"   • To check progress anytime: python tests/status.py")
        print(f"   • Results are stored in progress.db")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Critical error during demo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main demo function with user interaction."""
    print("🧪 SYSTEMATIC REVIEW DATA EXTRACTION - INTERACTIVE DEMO")
    print()
    
    try:
        # Get user preferences
        print("Demo Options:")
        print("1. Number of articles to process (default: 3)")
        num_input = input("Enter number of articles (or press Enter for default): ").strip()
        max_articles = int(num_input) if num_input.isdigit() and int(num_input) > 0 else 3
        
        print("\n2. Enable Google Sheets updates? (default: No - demo mode)")
        sheets_input = input("Update Google Sheets? (y/N): ").strip().lower()
        enable_sheets_update = sheets_input in ['y', 'yes', '1', 'true']
        
        if enable_sheets_update:
            print("⚠️  WARNING: This will modify your Google Sheets!")
            confirm = input("Are you sure? (y/N): ").strip().lower()
            enable_sheets_update = confirm in ['y', 'yes']
        
        print(f"\n🚀 Starting demo with {max_articles} articles...")
        print(f"Google Sheets updates: {'ENABLED' if enable_sheets_update else 'DISABLED'}")
        
        # Run the demo
        success = asyncio.run(run_full_demo(max_articles, enable_sheets_update))
        
        if success:
            print("\n🎉 Demo completed successfully!")
        else:
            print("\n⚠️  Demo encountered issues. Check the output above.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")

if __name__ == "__main__":
    main()
