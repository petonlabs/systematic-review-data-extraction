"""
Article fetcher for retrieving full-text content from various sources.
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse
import aiohttp
import requests
from pathlib import Path

from .config import FetcherConfig


class ArticleFetcher:
    """Fetch full-text articles from various sources."""
    
    def __init__(self, config: FetcherConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = None
        
        # Common headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_article(self, article: Dict[str, Any]) -> Optional[str]:
        """
        Fetch full-text content for an article.
        
        Args:
            article: Dictionary containing article metadata (DOI, PMID, etc.)
            
        Returns:
            Full-text content as string, or None if not found
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                headers=self.headers
            )
        
        doi = article.get('doi', '').strip()
        pmid = article.get('pmid', '').strip()
        url = article.get('url', '').strip()
        title = article.get('title', '').strip()
        
        self.logger.info(f"Fetching article: {title[:50]}...")
        
        # Try different sources in order of preference
        sources = [
            ('DOI direct', self._fetch_via_doi, doi),
            ('Direct URL', self._fetch_via_direct_url, url),
            ('Unpaywall', self._fetch_via_unpaywall, doi),
            ('CrossRef', self._fetch_via_crossref, doi),
            ('PubMed Central', self._fetch_via_pmc, pmid),
            ('Scopus URL', self._fetch_via_scopus_url, url),
            ('arXiv', self._fetch_via_arxiv, doi),
        ]
        
        for source_name, fetch_func, identifier in sources:
            if not identifier:
                continue
                
            try:
                self.logger.debug(f"Trying {source_name} for {identifier}")
                content = await fetch_func(identifier)
                
                if content and len(content.strip()) > 500:  # Minimum content threshold
                    self.logger.info(f"Successfully fetched from {source_name}")
                    return self._clean_text(content)
                    
            except Exception as e:
                self.logger.debug(f"Failed to fetch from {source_name}: {e}")
                continue
        
        # If all sources fail, try to get abstract/metadata only
        self.logger.warning("Could not fetch full text, trying metadata only")
        metadata = await self._fetch_metadata_only(doi, pmid)
        
        if metadata:
            return metadata
        
        self.logger.error("Could not fetch any content for article")
        return None
    
    async def _fetch_via_doi(self, doi: str) -> Optional[str]:
        """Try to fetch article directly via DOI."""
        if not doi:
            return None
        
        # Clean DOI
        doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        
        urls_to_try = [
            f"https://doi.org/{doi}",
            f"http://dx.doi.org/{doi}",
            f"https://www.doi.org/{doi}"
        ]
        
        for url in urls_to_try:
            try:
                async with self.session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Check if we got HTML content that might contain the article
                        if 'abstract' in content.lower() or 'article' in content.lower():
                            return self._extract_text_from_html(content)
                            
            except Exception as e:
                self.logger.debug(f"Error fetching via DOI {url}: {e}")
                continue
        
        return None
    
    async def _fetch_via_unpaywall(self, doi: str) -> Optional[str]:
        """Fetch open access version via Unpaywall API."""
        if not doi or not self.config.unpaywall_email:
            return None
        
        doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        url = f"https://api.unpaywall.org/v2/{doi}?email={self.config.unpaywall_email}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('is_oa', False):
                        # Try to get PDF or full text URL
                        oa_locations = data.get('oa_locations', [])
                        
                        for location in oa_locations:
                            pdf_url = location.get('url_for_pdf')
                            if pdf_url:
                                return await self._fetch_pdf_text(pdf_url)
                            
                            landing_url = location.get('url')
                            if landing_url:
                                return await self._fetch_from_url(landing_url)
        
        except Exception as e:
            self.logger.debug(f"Error with Unpaywall: {e}")
        
        return None
    
    async def _fetch_via_crossref(self, doi: str) -> Optional[str]:
        """Fetch metadata and try to get full text via CrossRef."""
        if not doi:
            return None
        
        doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        url = f"https://api.crossref.org/works/{doi}"
        
        if self.config.crossref_email:
            url += f"?mailto={self.config.crossref_email}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    work = data.get('message', {})
                    
                    # Get basic metadata
                    title = work.get('title', [''])[0]
                    abstract = work.get('abstract', '')
                    
                    # Try to get links to full text
                    links = work.get('link', [])
                    for link in links:
                        if link.get('content-type') == 'text/html':
                            content = await self._fetch_from_url(link.get('URL'))
                            if content:
                                return content
                    
                    # If no full text, return what we have
                    if title or abstract:
                        metadata = f"Title: {title}\n\n"
                        if abstract:
                            metadata += f"Abstract: {abstract}\n\n"
                        return metadata
        
        except Exception as e:
            self.logger.debug(f"Error with CrossRef: {e}")
        
        return None
    
    async def _fetch_via_pmc(self, pmid: str) -> Optional[str]:
        """Fetch from PubMed Central if available."""
        if not pmid:
            return None
        
        # First, check if PMC version exists
        pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmid}&format=json"
        
        try:
            async with self.session.get(pmc_url) as response:
                if response.status == 200:
                    data = await response.json()
                    records = data.get('records', [])
                    
                    for record in records:
                        pmcid = record.get('pmcid')
                        if pmcid:
                            # Try to get full text XML
                            xml_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/?tool=systematic_review&email=researcher@university.edu&format=xml"
                            return await self._fetch_from_url(xml_url)
        
        except Exception as e:
            self.logger.debug(f"Error with PMC: {e}")
        
        return None
    
    async def _fetch_via_arxiv(self, doi: str) -> Optional[str]:
        """Check if article is available on arXiv."""
        if not doi:
            return None
        
        # arXiv papers sometimes have DOIs, try to find via search
        arxiv_search_url = f"http://export.arxiv.org/api/query?search_query=doi:{doi}"
        
        try:
            async with self.session.get(arxiv_search_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse XML to find arXiv ID
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content)
                    
                    for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                        pdf_link = entry.find('.//{http://www.w3.org/2005/Atom}link[@type="application/pdf"]')
                        if pdf_link is not None:
                            pdf_url = pdf_link.get('href')
                            if pdf_url:
                                return await self._fetch_pdf_text(pdf_url)
        
        except Exception as e:
            self.logger.debug(f"Error with arXiv: {e}")
        
        return None
    
    async def _fetch_metadata_only(self, doi: str, pmid: str) -> Optional[str]:
        """Fetch basic metadata when full text is not available."""
        metadata_parts = []
        
        # Try PubMed for basic info
        if pmid:
            try:
                pubmed_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml&tool=systematic_review&email=researcher@university.edu"
                
                async with self.session.get(pubmed_url) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        # Extract title, abstract, etc. from XML
                        metadata = self._extract_pubmed_metadata(xml_content)
                        if metadata:
                            metadata_parts.append(metadata)
            
            except Exception as e:
                self.logger.debug(f"Error fetching PubMed metadata: {e}")
        
        return '\n\n'.join(metadata_parts) if metadata_parts else None
    
    def _extract_pubmed_metadata(self, xml_content: str) -> str:
        """Extract basic metadata from PubMed XML."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            parts = []
            
            # Title
            title_elem = root.find('.//ArticleTitle')
            if title_elem is not None and title_elem.text:
                parts.append(f"Title: {title_elem.text}")
            
            # Abstract
            abstract_elem = root.find('.//AbstractText')
            if abstract_elem is not None and abstract_elem.text:
                parts.append(f"Abstract: {abstract_elem.text}")
            
            # Keywords
            keyword_elems = root.findall('.//Keyword')
            if keyword_elems:
                keywords = [kw.text for kw in keyword_elems if kw.text]
                if keywords:
                    parts.append(f"Keywords: {', '.join(keywords)}")
            
            return '\n\n'.join(parts)
        
        except Exception as e:
            self.logger.debug(f"Error parsing PubMed XML: {e}")
            return ''
    
    async def _fetch_from_url(self, url: str) -> Optional[str]:
        """Generic URL fetching with retries."""
        for attempt in range(self.config.max_retries):
            try:
                async with self.session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        
                        if 'text/html' in content_type:
                            text = await response.text()
                            return self._extract_text_from_html(text)
                        elif 'xml' in content_type:
                            text = await response.text()
                            return self._extract_text_from_xml(text)
                        elif 'pdf' in content_type:
                            # Handle PDF content
                            return await self._fetch_pdf_text(url)
                        else:
                            text = await response.text()
                            return text
            
            except Exception as e:
                self.logger.debug(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    async def _fetch_pdf_text(self, pdf_url: str) -> Optional[str]:
        """Fetch and extract text from PDF (placeholder - would need PDF parsing library)."""
        self.logger.debug(f"PDF extraction not yet implemented for {pdf_url}")
        # Would integrate with PyPDF2, pdfplumber, or similar
        return None
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract readable text from HTML content."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Get text from main content areas
            main_content = soup.find('main') or soup.find('article') or soup
            
            # Extract text
            text = main_content.get_text()
            
            return self._clean_text(text)
        
        except ImportError:
            self.logger.warning("BeautifulSoup not available, returning raw HTML")
            return html_content
        except Exception as e:
            self.logger.debug(f"Error extracting HTML text: {e}")
            return html_content
    
    def _extract_text_from_xml(self, xml_content: str) -> str:
        """Extract text from XML content."""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            # Extract all text content
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())
            
            return self._clean_text(' '.join(text_parts))
        
        except Exception as e:
            self.logger.debug(f"Error parsing XML: {e}")
            return xml_content
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove non-printable characters
        text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
    
    async def _fetch_via_direct_url(self, url: str) -> Optional[str]:
        """Fetch article content directly from a URL."""
        if not url:
            return None
        
        self.logger.debug(f"Attempting to fetch directly from URL: {url}")
        
        try:
            # Try to fetch the content directly
            return await self._fetch_from_url(url)
        
        except Exception as e:
            self.logger.debug(f"Error fetching from direct URL: {e}")
            return None
    
    async def _fetch_via_scopus_url(self, url: str) -> Optional[str]:
        """Fetch article content from Scopus URL."""
        if not url or 'scopus.com' not in url.lower():
            return None
        
        self.logger.debug(f"Attempting to fetch from Scopus URL: {url}")
        
        try:
            # For Scopus URLs, we need to handle them specially
            # Scopus URLs often redirect to the full text or abstract
            return await self._fetch_from_url(url)
        
        except Exception as e:
            self.logger.debug(f"Error fetching from Scopus URL: {e}")
            return None
