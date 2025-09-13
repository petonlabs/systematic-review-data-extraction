#!/usr/bin/env python3
"""Test URL handling in the article fetcher."""

import asyncio
import logging
from dotenv import load_dotenv
from src.article_fetcher import ArticleFetcher
from src.config import Config

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)

async def test_url_handling():
    """Test the URL handling functionality."""
    config = Config()
    
    # Initialize the config to make sure all attributes are available
    config.validate()
    
    fetcher = ArticleFetcher(config)
    
    # Test articles with different URL types
    test_articles = [
        {
            'title': 'Test Article with Direct URL',
            'doi': '',  # No DOI
            'pmid': '',  # No PMID
            'url': 'https://pubmed.ncbi.nlm.nih.gov/39245054/'  # Direct URL
        },
        {
            'title': 'Test Article with Scopus URL',
            'doi': '',  # No DOI
            'pmid': '',  # No PMID
            'url': 'https://www.scopus.com/inward/record.uri?eid=2-s2.0-85123456789&partnerID=40&md5=abc123'  # Scopus URL
        }
    ]
    
    for i, article in enumerate(test_articles, 1):
        print(f"\n{'='*60}")
        print(f"Testing article {i}: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"{'='*60}")
        
        try:
            # Test the new URL handling
            async with ArticleFetcher(config) as fetcher:
                content = await fetcher.fetch_article(article)
            
            if content:
                print(f"✅ Successfully fetched content ({len(content)} characters)")
                print(f"First 200 chars: {content[:200]}...")
            else:
                print("❌ No content fetched")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*60}")
    print("URL handling test completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(test_url_handling())
