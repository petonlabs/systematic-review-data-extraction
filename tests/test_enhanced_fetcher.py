#!/usr/bin/env python3
"""
Enhanced article fetcher with multiple fallback strategies for failed articles.
"""

import asyncio
import aiohttp
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.sheets_client import SheetsClient


class EnhancedArticleFetcher:
    """Enhanced article fetcher with multiple retrieval strategies."""
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_article_enhanced(self, article: Dict[str, Any]) -> Optional[str]:
        """Enhanced article fetching with multiple strategies."""
        title = article.get('title', '')
        doi = article.get('doi', '')
        url = article.get('url', '')
        abstract = article.get('abstract_note', '')
        
        print(f"🔍 Trying to fetch: {title[:60]}...")
        
        # Strategy 1: Direct DOI resolution
        if doi:
            content = await self._fetch_from_doi(doi)
            if content:
                print(f"✅ Retrieved via DOI: {len(content)} chars")
                return content
        
        # Strategy 2: PubMed extraction
        if 'pubmed' in url.lower():
            content = await self._fetch_from_pubmed_url(url)
            if content:
                print(f"✅ Retrieved via PubMed: {len(content)} chars")
                return content
        
        # Strategy 3: CrossRef API
        if doi:
            content = await self._fetch_from_crossref(doi)
            if content:
                print(f"✅ Retrieved via CrossRef: {len(content)} chars")
                return content
        
        # Strategy 4: Alternative URL processing
        if url and not 'scopus' in url.lower():
            content = await self._fetch_from_alternative_url(url)
            if content:
                print(f"✅ Retrieved via alternative URL: {len(content)} chars")
                return content
        
        # Strategy 5: Use abstract + metadata if available
        if abstract and len(abstract) > 100:
            enhanced_content = self._create_content_from_metadata(article)
            print(f"✅ Created content from metadata: {len(enhanced_content)} chars")
            return enhanced_content
        
        print(f"❌ Could not retrieve content for: {title[:60]}...")
        return None
    
    async def _fetch_from_doi(self, doi: str) -> Optional[str]:
        """Fetch content using DOI resolution."""
        if not doi or doi == 'No DOI':
            return None
            
        try:
            # Try DOI.org resolution
            doi_url = f"https://doi.org/{doi}"
            async with self.session.get(doi_url, allow_redirects=True) as response:
                if response.status == 200:
                    content = await response.text()
                    # Extract meaningful content
                    extracted = self._extract_article_content(content)
                    if extracted and len(extracted) > 200:
                        return extracted
        except Exception as e:
            print(f"   DOI fetch failed: {e}")
        return None
    
    async def _fetch_from_pubmed_url(self, url: str) -> Optional[str]:
        """Enhanced PubMed content extraction."""
        if not url or 'pubmed' not in url.lower():
            return None
            
        try:
            # Extract PMID from URL
            pmid_match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', url)
            if pmid_match:
                pmid = pmid_match.group(1)
                # Try PubMed API
                api_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
                async with self.session.get(api_url) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        extracted = self._extract_from_pubmed_xml(xml_content)
                        if extracted:
                            return extracted
        except Exception as e:
            print(f"   PubMed fetch failed: {e}")
        return None
    
    async def _fetch_from_crossref(self, doi: str) -> Optional[str]:
        """Fetch metadata from CrossRef API."""
        if not doi:
            return None
            
        try:
            crossref_url = f"https://api.crossref.org/works/{doi}"
            async with self.session.get(crossref_url) as response:
                if response.status == 200:
                    import json
                    data = await response.json()
                    work = data.get('message', {})
                    
                    # Extract available information
                    title = work.get('title', [''])[0]
                    abstract = work.get('abstract', '')
                    
                    if abstract:
                        # Clean HTML tags from abstract
                        clean_abstract = re.sub(r'<[^>]+>', '', abstract)
                        if len(clean_abstract) > 100:
                            return f"Title: {title}\n\nAbstract: {clean_abstract}"
        except Exception as e:
            print(f"   CrossRef fetch failed: {e}")
        return None
    
    async def _fetch_from_alternative_url(self, url: str) -> Optional[str]:
        """Try alternative URL fetching strategies."""
        if not url or 'scopus' in url.lower():
            return None
            
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    content = await response.text()
                    extracted = self._extract_article_content(content)
                    if extracted and len(extracted) > 200:
                        return extracted
        except Exception as e:
            print(f"   Alternative URL fetch failed: {e}")
        return None
    
    def _create_content_from_metadata(self, article: Dict[str, Any]) -> str:
        """Create extraction content from available metadata."""
        parts = []
        
        if article.get('title'):
            parts.append(f"Title: {article['title']}")
        
        if article.get('abstract_note'):
            parts.append(f"Abstract: {article['abstract_note']}")
        
        if article.get('publication_title'):
            parts.append(f"Journal: {article['publication_title']}")
        
        if article.get('publication_year'):
            parts.append(f"Year: {article['publication_year']}")
        
        # Add any additional relevant metadata
        for field in ['pages', 'volume', 'issue', 'journal_abbreviation']:
            if article.get(field):
                parts.append(f"{field.title()}: {article[field]}")
        
        return "\n\n".join(parts)
    
    def _extract_article_content(self, html_content: str) -> Optional[str]:
        """Extract meaningful content from HTML."""
        if not html_content:
            return None
        
        # Remove HTML tags and extract text
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Look for abstract or content sections
        abstract_match = re.search(r'abstract[:\s]*(.{200,2000})', text, re.IGNORECASE)
        if abstract_match:
            return f"Content: {abstract_match.group(1).strip()}"
        
        # Return first substantial paragraph if no abstract found
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 100]
        if paragraphs:
            return f"Content: {paragraphs[0][:1500]}"
        
        return None
    
    def _extract_from_pubmed_xml(self, xml_content: str) -> Optional[str]:
        """Extract content from PubMed XML."""
        if not xml_content:
            return None
        
        # Simple XML parsing for abstract
        abstract_match = re.search(r'<AbstractText[^>]*>(.*?)</AbstractText>', xml_content, re.DOTALL | re.IGNORECASE)
        title_match = re.search(r'<ArticleTitle>(.*?)</ArticleTitle>', xml_content, re.IGNORECASE)
        
        parts = []
        if title_match:
            title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
            parts.append(f"Title: {title}")
        
        if abstract_match:
            abstract = re.sub(r'<[^>]+>', '', abstract_match.group(1)).strip()
            parts.append(f"Abstract: {abstract}")
        
        return "\n\n".join(parts) if parts else None


async def test_enhanced_fetcher():
    """Test the enhanced fetcher on failed articles."""
    print("🧪 Testing Enhanced Article Fetcher")
    print("=" * 50)
    
    try:
        config = Config()
        sheets_client = SheetsClient(config.sheets_config)
        
        # Get all articles
        all_articles = await sheets_client.get_articles()
        
        # Focus on the recently failed articles (IDs 32-36)
        failed_ids = ['32', '33', '34', '35', '36']
        test_articles = []
        
        for i, article in enumerate(all_articles):
            article_id = str(i + 1)
            if article_id in failed_ids:
                test_articles.append((article_id, article))
        
        async with EnhancedArticleFetcher() as fetcher:
            successes = 0
            for article_id, article in test_articles:
                print(f"\n🔍 Testing Article {article_id}: {article.get('title', 'No title')[:60]}...")
                
                content = await fetcher.fetch_article_enhanced(article)
                if content:
                    successes += 1
                    print(f"✅ SUCCESS: Retrieved {len(content)} characters")
                    # Show preview
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"   Preview: {preview}")
                else:
                    print(f"❌ FAILED: Could not retrieve content")
                
                print("-" * 50)
            
            print(f"\n📊 Results: {successes}/{len(test_articles)} articles successfully retrieved")
            print(f"   Success rate: {(successes/len(test_articles)*100):.1f}%")
            
            if successes > 0:
                print("\n💡 The enhanced fetcher can recover some failed articles!")
                print("   Consider integrating these strategies into the main ArticleFetcher.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enhanced_fetcher())
