"""
Enhanced article fetcher with PDF-first capabilities and Cloudflare R2 integration.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, Union
from pathlib import Path

from .article_fetcher import ArticleFetcher as BaseArticleFetcher
from .pdf_processor import PdfProcessor
from .cloudflare_r2 import CloudflareR2Storage
from .config import Config, FetcherConfig, PdfConfig, R2Config
from .extraction_mode_manager import ExtractionMethod


class EnhancedArticleFetcher(BaseArticleFetcher):
    """Enhanced article fetcher with PDF-first capabilities."""
    
    def __init__(self, config: Config, extraction_method: ExtractionMethod = ExtractionMethod.WEB_BASED):
        super().__init__(config.fetcher_config)
        
        self.config = config
        self.extraction_method = extraction_method
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize PDF components if using PDF method
        self.pdf_processor = None
        self.r2_storage = None
        
        if extraction_method == ExtractionMethod.PDF_BASED:
            self.pdf_processor = PdfProcessor(config.pdf_config)
            
            # Only initialize R2 if properly configured
            if config.validate_r2_config():
                self.r2_storage = CloudflareR2Storage(config.r2_config)
                self.logger.info("R2 storage initialized for PDF-based extraction")
            else:
                self.logger.warning("R2 not configured - PDFs will be processed locally only")
        
        self.logger.info(f"Enhanced article fetcher initialized with {extraction_method.value} method")
    
    async def fetch_article(self, article: Dict[str, Any]) -> Optional[Union[str, Tuple[str, Dict[str, Any]]]]:
        """
        Fetch article content using the configured method.
        
        Args:
            article: Article metadata dictionary
            
        Returns:
            Extracted text content, or tuple of (text, metadata) for PDF method
        """
        article_title = article.get('title', 'Unknown Article')[:50]
        self.logger.info(f"Fetching article using {self.extraction_method.value} method: {article_title}...")
        
        if self.extraction_method == ExtractionMethod.PDF_BASED:
            return await self._fetch_pdf_based(article)
        else:
            return await self._fetch_web_based(article)
    
    async def _fetch_web_based(self, article: Dict[str, Any]) -> Optional[str]:
        """Fetch article using traditional web-based method."""
        try:
            return await super().fetch_article(article)
        except Exception as e:
            self.logger.error(f"Web-based fetching failed: {e}")
            return None
    
    async def _fetch_pdf_based(self, article: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Fetch article using PDF-first approach.
        
        Returns:
            Tuple of (extracted_text, metadata) or None if failed
        """
        article_id = article.get('id', f"article_{hash(str(article))}")
        
        try:
            # Step 1: Try to get PDF from R2 storage if available
            if self.r2_storage and await self.r2_storage.test_connection():
                stored_pdf = await self._try_retrieve_stored_pdf(article)
                if stored_pdf:
                    text, metadata = stored_pdf
                    self.logger.info("Successfully retrieved and processed PDF from R2 storage")
                    return text, metadata
            
            # Step 2: Try to fetch PDF from various sources
            pdf_content = await self._fetch_pdf_content(article)
            if not pdf_content:
                # Fallback to web-based extraction if no PDF available
                self.logger.info("No PDF available, falling back to web-based extraction")
                text_content = await self._fetch_web_based(article)
                if text_content:
                    return text_content, article
                return None
            
            # Step 3: Store PDF in R2 if configured
            r2_key = None
            if self.r2_storage:
                try:
                    r2_key = await self.r2_storage.store_pdf(pdf_content, article)
                    if r2_key:
                        self.logger.info(f"Stored PDF in R2: {r2_key}")
                except Exception as e:
                    self.logger.warning(f"Failed to store PDF in R2: {e}")
            
            # Step 4: Extract text from PDF
            if not self.pdf_processor:
                self.logger.error("PDF processor not available")
                return None
            
            extracted_text = await self.pdf_processor.extract_text_from_pdf(pdf_content, article)
            if not extracted_text:
                self.logger.warning("No text extracted from PDF, falling back to web method")
                fallback_text = await self._fetch_web_based(article)
                if fallback_text:
                    return fallback_text, article
                return None
            
            # Step 5: Prepare metadata
            pdf_metadata = self.pdf_processor.get_pdf_metadata(pdf_content)
            combined_metadata = {**article, **pdf_metadata}
            if r2_key:
                combined_metadata['r2_key'] = r2_key
                combined_metadata['pdf_stored'] = True
            
            self.logger.info(f"Successfully processed PDF: {len(extracted_text)} characters extracted")
            return extracted_text, combined_metadata
            
        except Exception as e:
            self.logger.error(f"PDF-based fetching failed for {article_id}: {e}")
            
            # Final fallback to web-based method
            try:
                self.logger.info("Attempting fallback to web-based extraction")
                fallback_text = await self._fetch_web_based(article)
                if fallback_text:
                    return fallback_text, article
            except Exception as fallback_error:
                self.logger.error(f"Fallback also failed: {fallback_error}")
            
            return None
    
    async def _try_retrieve_stored_pdf(self, article: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Try to retrieve and process a previously stored PDF."""
        try:
            # Generate expected R2 key for this article
            expected_key = self.r2_storage._generate_pdf_key(article)
            
            # Try to retrieve PDF content
            pdf_content = await self.r2_storage.retrieve_pdf(expected_key)
            if not pdf_content:
                return None
            
            # Extract text from stored PDF
            extracted_text = await self.pdf_processor.extract_text_from_pdf(pdf_content, article)
            if not extracted_text:
                return None
            
            # Get stored metadata
            r2_metadata = await self.r2_storage.get_pdf_metadata(expected_key)
            combined_metadata = {**article, **r2_metadata}
            combined_metadata['r2_key'] = expected_key
            combined_metadata['pdf_stored'] = True
            combined_metadata['source'] = 'r2_storage'
            
            return extracted_text, combined_metadata
            
        except Exception as e:
            self.logger.debug(f"Could not retrieve stored PDF: {e}")
            return None
    
    async def _fetch_pdf_content(self, article: Dict[str, Any]) -> Optional[bytes]:
        """
        Fetch PDF content from various sources.
        
        Args:
            article: Article metadata
            
        Returns:
            PDF content as bytes, or None if not found
        """
        doi = article.get('doi', '').strip()
        pmid = article.get('pmid', '').strip()
        url = article.get('url', '').strip()
        
        # Sources to try for PDF content (in order of preference)
        pdf_sources = []
        
        # Add DOI-based PDF sources
        if doi:
            cleaned_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
            pdf_sources.extend([
                ('DOI PDF direct', self._fetch_pdf_via_doi, cleaned_doi),
                ('Unpaywall PDF', self._fetch_pdf_via_unpaywall, cleaned_doi)
            ])
        
        # Add URL-based sources
        if url:
            pdf_sources.append(('Direct URL PDF', self._fetch_pdf_via_url, url))
        
        # Add PMC PDF source
        if pmid:
            pdf_sources.append(('PMC PDF', self._fetch_pdf_via_pmc, pmid))
        
        # Add arXiv PDF source
        if doi:
            pdf_sources.append(('arXiv PDF', self._fetch_pdf_via_arxiv, doi))
        
        # Try each source
        for source_name, fetch_func, identifier in pdf_sources:
            if not identifier:
                continue
                
            try:
                self.logger.debug(f"Trying {source_name} for PDF")
                pdf_content = await fetch_func(identifier)
                
                if pdf_content and self.pdf_processor and self.pdf_processor.validate_pdf(pdf_content):
                    self.logger.info(f"Successfully fetched PDF from {source_name}")
                    return pdf_content
                    
            except Exception as e:
                self.logger.debug(f"Failed to fetch PDF from {source_name}: {e}")
                continue
        
        self.logger.warning("No PDF content found from any source")
        return None
    
    async def _fetch_pdf_via_doi(self, doi: str) -> Optional[bytes]:
        """Fetch PDF directly via DOI resolution."""
        pdf_urls = [
            f"https://doi.org/{doi}",
            f"http://dx.doi.org/{doi}"
        ]
        
        for url in pdf_urls:
            try:
                async with self.session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '').lower()
                        if 'application/pdf' in content_type:
                            return await response.read()
                        
                        # Sometimes PDFs are served with incorrect MIME type
                        content = await response.read()
                        if content.startswith(b'%PDF'):
                            return content
                            
            except Exception as e:
                self.logger.debug(f"Error fetching PDF via DOI {url}: {e}")
                continue
        
        return None
    
    async def _fetch_pdf_via_unpaywall(self, doi: str) -> Optional[bytes]:
        """Fetch PDF via Unpaywall API."""
        if not self.config.fetcher_config.unpaywall_email:
            return None
        
        try:
            # First get the Unpaywall data
            unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email={self.config.fetcher_config.unpaywall_email}"
            
            async with self.session.get(unpaywall_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('is_oa', False):
                        oa_locations = data.get('oa_locations', [])
                        
                        # Try PDF URLs from OA locations
                        for location in oa_locations:
                            pdf_url = location.get('url_for_pdf')
                            if pdf_url:
                                pdf_content = await self._download_pdf_from_url(pdf_url)
                                if pdf_content:
                                    return pdf_content
        
        except Exception as e:
            self.logger.debug(f"Error with Unpaywall PDF: {e}")
        
        return None
    
    async def _fetch_pdf_via_url(self, url: str) -> Optional[bytes]:
        """Fetch PDF from direct URL."""
        return await self._download_pdf_from_url(url)
    
    async def _fetch_pdf_via_pmc(self, pmid: str) -> Optional[bytes]:
        """Fetch PDF from PubMed Central."""
        try:
            # Get PMC ID from PMID
            conversion_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmid}&format=json"
            
            async with self.session.get(conversion_url) as response:
                if response.status == 200:
                    data = await response.json()
                    records = data.get('records', [])
                    
                    for record in records:
                        pmcid = record.get('pmcid')
                        if pmcid:
                            # Try to get PDF from PMC
                            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/"
                            pdf_content = await self._download_pdf_from_url(pdf_url)
                            if pdf_content:
                                return pdf_content
        
        except Exception as e:
            self.logger.debug(f"Error fetching PDF from PMC: {e}")
        
        return None
    
    async def _fetch_pdf_via_arxiv(self, doi: str) -> Optional[bytes]:
        """Fetch PDF from arXiv if available."""
        try:
            # Search for arXiv paper by DOI
            search_url = f"http://export.arxiv.org/api/query?search_query=doi:{doi}"
            
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse XML to find PDF links
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(content)
                    
                    for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                        pdf_link = entry.find('.//{http://www.w3.org/2005/Atom}link[@type="application/pdf"]')
                        if pdf_link is not None:
                            pdf_url = pdf_link.get('href')
                            if pdf_url:
                                pdf_content = await self._download_pdf_from_url(pdf_url)
                                if pdf_content:
                                    return pdf_content
        
        except Exception as e:
            self.logger.debug(f"Error fetching PDF from arXiv: {e}")
        
        return None
    
    async def _download_pdf_from_url(self, url: str) -> Optional[bytes]:
        """Download PDF content from a URL."""
        try:
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    content = await response.read()
                    
                    # Check if it's actually a PDF
                    if 'application/pdf' in content_type or content.startswith(b'%PDF'):
                        # Check file size limits
                        max_size = self.config.r2_config.max_file_size_mb * 1024 * 1024
                        if len(content) > max_size:
                            self.logger.warning(f"PDF too large ({len(content)} bytes), skipping")
                            return None
                        
                        return content
        
        except Exception as e:
            self.logger.debug(f"Error downloading PDF from {url}: {e}")
        
        return None