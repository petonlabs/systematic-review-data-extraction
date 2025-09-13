#!/usr/bin/env python3
"""Quick test of fixed article fetcher."""

import asyncio
import logging
from dotenv import load_dotenv
from src.config import Config
from src.article_fetcher import ArticleFetcher

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

async def test_single_article():
    """Test fetching a single article."""
    config = Config()
    
    # Test article with DOI
    test_article = {
        'title': 'Test Article with DOI',
        'doi': '10.1016/S2214-109X(24)00330-9',
        'pmid': '39245054',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/39245054/'
    }
    
    print(f"Testing article: {test_article['title']}")
    print(f"DOI: {test_article['doi']}")
    
    try:
        async with ArticleFetcher(config.fetcher_config) as fetcher:
            content = await fetcher.fetch_article(test_article)
        
        if content:
            print(f"✅ Successfully fetched content ({len(content)} characters)")
            print(f"First 200 chars: {content[:200]}...")
        else:
            print("❌ No content fetched")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_single_article())
