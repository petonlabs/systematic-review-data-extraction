"""
PDF processor for extracting text from PDF documents with memory-efficient operations.
"""

import io
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path
import tempfile
import os

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logging.warning("pdfplumber not available - PDF processing will be limited")

from .config import PdfConfig


class PdfProcessor:
    """Handle PDF text extraction with memory-efficient operations."""
    
    def __init__(self, config: PdfConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not HAS_PDFPLUMBER:
            self.logger.warning("PDF processing libraries not available")
    
    async def extract_text_from_pdf(
        self, 
        pdf_content: Union[bytes, str, Path], 
        source_info: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Extract text from PDF with memory-efficient operations.
        
        Args:
            pdf_content: PDF content as bytes, file path, or file-like object
            source_info: Optional metadata about the source
            
        Returns:
            Extracted text or None if extraction fails
        """
        if not HAS_PDFPLUMBER:
            self.logger.error("PDF processing libraries not available")
            return None
        
        source_description = source_info.get('title', 'Unknown') if source_info else 'Unknown'
        self.logger.info(f"Extracting text from PDF: {source_description[:50]}...")
        
        try:
            # Handle different input types
            if isinstance(pdf_content, (str, Path)):
                # File path
                pdf_path = Path(pdf_content)
                if not pdf_path.exists():
                    self.logger.error(f"PDF file not found: {pdf_path}")
                    return None
                return await self._extract_from_file(pdf_path)
            
            elif isinstance(pdf_content, bytes):
                # Bytes content - use temporary file for memory efficiency
                return await self._extract_from_bytes(pdf_content)
            
            else:
                self.logger.error(f"Unsupported PDF content type: {type(pdf_content)}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {e}")
            return None
    
    async def _extract_from_file(self, pdf_path: Path) -> Optional[str]:
        """Extract text from PDF file with memory management."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return await self._extract_text_from_pdf_object(pdf, str(pdf_path))
        except Exception as e:
            self.logger.error(f"Error reading PDF file {pdf_path}: {e}")
            return None
    
    async def _extract_from_bytes(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract text from PDF bytes using temporary file for memory efficiency."""
        temp_file = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_bytes)
                temp_file_path = temp_file.name
            
            # Extract text from temporary file
            result = await self._extract_from_file(Path(temp_file_path))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing PDF bytes: {e}")
            return None
        finally:
            # Clean up temporary file
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception as cleanup_error:
                    self.logger.warning(f"Could not clean up temp file: {cleanup_error}")
    
    async def _extract_text_from_pdf_object(self, pdf, source_name: str) -> Optional[str]:
        """Extract text from opened PDF object with pagination and memory management."""
        try:
            pages_text = []
            total_pages = len(pdf.pages)
            
            self.logger.info(f"Processing {total_pages} pages from {source_name}")
            
            # Process pages in chunks to manage memory
            chunk_size = self.config.page_chunk_size
            for start_page in range(0, total_pages, chunk_size):
                end_page = min(start_page + chunk_size, total_pages)
                
                # Process chunk of pages
                chunk_text = []
                for page_num in range(start_page, end_page):
                    try:
                        page = pdf.pages[page_num]
                        page_text = page.extract_text()
                        
                        if page_text:
                            # Clean and validate page text
                            cleaned_text = self._clean_page_text(page_text)
                            if cleaned_text and len(cleaned_text.strip()) > self.config.min_page_text_length:
                                chunk_text.append(cleaned_text)
                        
                        # Check if we've reached maximum text length
                        current_length = sum(len(text) for text in pages_text + chunk_text)
                        if current_length > self.config.max_text_length:
                            self.logger.info(f"Reached maximum text length ({self.config.max_text_length} chars), stopping extraction")
                            break
                            
                    except Exception as page_error:
                        self.logger.warning(f"Error extracting page {page_num + 1}: {page_error}")
                        continue
                
                pages_text.extend(chunk_text)
                
                # Check total length after each chunk
                total_length = sum(len(text) for text in pages_text)
                if total_length > self.config.max_text_length:
                    break
                    
                self.logger.debug(f"Processed pages {start_page + 1}-{end_page}, total length: {total_length}")
            
            if not pages_text:
                self.logger.warning("No text extracted from PDF")
                return None
            
            # Combine all pages
            full_text = "\n\n".join(pages_text)
            
            # Final cleanup and validation
            final_text = self._post_process_text(full_text)
            
            self.logger.info(f"Successfully extracted {len(final_text)} characters from PDF")
            return final_text
            
        except Exception as e:
            self.logger.error(f"Error during text extraction: {e}")
            return None
    
    def _clean_page_text(self, text: str) -> str:
        """Clean individual page text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove non-printable characters except newlines and tabs
        text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
        
        return text.strip()
    
    def _post_process_text(self, text: str) -> str:
        """Final text processing and cleanup."""
        if not text:
            return ""
        
        import re
        
        # Normalize line breaks and excessive spacing
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove page headers/footers that commonly repeat
        # This is a basic implementation - can be enhanced
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 3:  # Skip very short lines that might be artifacts
                cleaned_lines.append(line)
        
        final_text = '\n'.join(cleaned_lines)
        
        # Truncate if too long
        if len(final_text) > self.config.max_text_length:
            final_text = final_text[:self.config.max_text_length] + "\n[Text truncated due to length limit]"
            self.logger.info(f"Text truncated to {self.config.max_text_length} characters")
        
        return final_text.strip()
    
    def validate_pdf(self, pdf_content: bytes) -> bool:
        """Validate that content is a valid PDF."""
        try:
            # Basic PDF signature check
            if pdf_content.startswith(b'%PDF'):
                return True
            
            self.logger.warning("Content does not appear to be a valid PDF")
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating PDF: {e}")
            return False
    
    def get_pdf_metadata(self, pdf_content: Union[bytes, str, Path]) -> Dict[str, Any]:
        """Extract metadata from PDF."""
        if not HAS_PDFPLUMBER:
            return {}
        
        metadata = {}
        
        try:
            if isinstance(pdf_content, bytes):
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=True) as temp_file:
                    temp_file.write(pdf_content)
                    temp_file.flush()
                    
                    with pdfplumber.open(temp_file.name) as pdf:
                        metadata.update(self._extract_metadata_from_pdf(pdf))
            
            elif isinstance(pdf_content, (str, Path)):
                with pdfplumber.open(pdf_content) as pdf:
                    metadata.update(self._extract_metadata_from_pdf(pdf))
                    
        except Exception as e:
            self.logger.warning(f"Could not extract PDF metadata: {e}")
        
        return metadata
    
    def _extract_metadata_from_pdf(self, pdf) -> Dict[str, Any]:
        """Extract metadata from opened PDF."""
        metadata = {}
        
        try:
            # Basic metadata
            if hasattr(pdf, 'metadata') and pdf.metadata:
                metadata.update({
                    'title': pdf.metadata.get('Title', ''),
                    'author': pdf.metadata.get('Author', ''),
                    'subject': pdf.metadata.get('Subject', ''),
                    'creator': pdf.metadata.get('Creator', ''),
                    'producer': pdf.metadata.get('Producer', ''),
                    'creation_date': str(pdf.metadata.get('CreationDate', '')),
                    'modification_date': str(pdf.metadata.get('ModDate', ''))
                })
            
            # Page count and other structural info
            metadata.update({
                'page_count': len(pdf.pages),
                'has_text': any(page.extract_text() for page in pdf.pages[:3])  # Check first 3 pages
            })
            
        except Exception as e:
            self.logger.warning(f"Error extracting PDF metadata: {e}")
        
        return metadata