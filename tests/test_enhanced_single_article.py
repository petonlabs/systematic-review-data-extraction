#!/usr/bin/env python3
"""Enhanced test for single article processing with both extraction methods."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.config import Config
from src.enhanced_article_fetcher import EnhancedArticleFetcher
from src.extraction_mode_manager import ExtractionMethod

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)


async def test_single_article_both_methods():
    """Test fetching a single article with both extraction methods."""
    config = Config()
    
    # Test article with DOI
    test_article = {
        'id': 'test_single_001',
        'title': 'Test Article with DOI',
        'doi': '10.1016/S2214-109X(24)00330-9',
        'pmid': '39245054',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/39245054/'
    }
    
    print(f"Testing article: {test_article['title']}")
    print(f"DOI: {test_article['doi']}")
    print(f"PMID: {test_article['pmid']}")
    
    # Test web-based method
    print("\n" + "="*60)
    print("Testing WEB-BASED extraction method")
    print("="*60)
    
    try:
        async with EnhancedArticleFetcher(config, ExtractionMethod.WEB_BASED) as web_fetcher:
            web_content = await web_fetcher.fetch_article(test_article)
        
        if web_content:
            print(f"✅ Web-based: Successfully fetched content ({len(web_content)} characters)")
            print(f"First 200 chars: {web_content[:200]}...")
        else:
            print("❌ Web-based: No content fetched")
            
    except Exception as e:
        print(f"❌ Web-based error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test PDF-based method
    print("\n" + "="*60)
    print("Testing PDF-BASED extraction method")
    print("="*60)
    
    try:
        async with EnhancedArticleFetcher(config, ExtractionMethod.PDF_BASED) as pdf_fetcher:
            pdf_result = await pdf_fetcher.fetch_article(test_article)
        
        if pdf_result:
            if isinstance(pdf_result, tuple):
                pdf_content, metadata = pdf_result
                print(f"✅ PDF-based: Successfully fetched content ({len(pdf_content)} characters)")
                print(f"📊 Metadata fields: {list(metadata.keys())}")
                if metadata.get('pdf_stored'):
                    print(f"📁 PDF stored in R2: {metadata.get('r2_key', 'Unknown key')}")
                print(f"First 200 chars: {pdf_content[:200]}...")
            else:
                print(f"✅ PDF-based: Successfully fetched content ({len(pdf_result)} characters)")
                print(f"First 200 chars: {pdf_result[:200]}...")
        else:
            print("❌ PDF-based: No content fetched")
            
    except Exception as e:
        print(f"❌ PDF-based error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)


async def test_pdf_availability():
    """Test PDF sources for the article."""
    config = Config()
    
    test_article = {
        'id': 'test_pdf_availability',
        'title': 'Test PDF Availability',
        'doi': '10.1016/S2214-109X(24)00330-9',
        'pmid': '39245054'
    }
    
    print("\n📋 Testing PDF source availability...")
    
    try:
        async with EnhancedArticleFetcher(config, ExtractionMethod.PDF_BASED) as pdf_fetcher:
            # Test individual PDF sources
            sources_to_test = [
                ('DOI PDF', pdf_fetcher._fetch_pdf_via_doi, test_article.get('doi')),
                ('Unpaywall PDF', pdf_fetcher._fetch_pdf_via_unpaywall, test_article.get('doi')),
                ('PMC PDF', pdf_fetcher._fetch_pdf_via_pmc, test_article.get('pmid'))
            ]
            
            for source_name, fetch_method, identifier in sources_to_test:
                if not identifier:
                    print(f"⏭️  {source_name}: No identifier available")
                    continue
                
                try:
                    print(f"🔍 Testing {source_name}...")
                    pdf_content = await fetch_method(identifier)
                    
                    if pdf_content:
                        print(f"✅ {source_name}: Found PDF ({len(pdf_content)} bytes)")
                        
                        # Test PDF validation
                        if pdf_fetcher.pdf_processor and pdf_fetcher.pdf_processor.validate_pdf(pdf_content):
                            print(f"✅ {source_name}: PDF validation passed")
                        else:
                            print(f"⚠️  {source_name}: PDF validation failed")
                    else:
                        print(f"❌ {source_name}: No PDF found")
                        
                except Exception as e:
                    print(f"❌ {source_name}: Error - {e}")
    
    except Exception as e:
        print(f"❌ Error testing PDF availability: {e}")


if __name__ == "__main__":
    print("🧪 Enhanced Single Article Test")
    print("Testing both web-based and PDF-based extraction methods")
    
    asyncio.run(test_single_article_both_methods())
    asyncio.run(test_pdf_availability())