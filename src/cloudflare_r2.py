"""
Cloudflare R2 storage client for managing PDF files.
"""

import asyncio
import io
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    logging.warning("boto3 not available - R2 storage will not work")

from .config import R2Config


class CloudflareR2Storage:
    """Handle Cloudflare R2 storage operations for PDF files."""
    
    def __init__(self, config: R2Config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = None
        
        if not HAS_BOTO3:
            self.logger.error("boto3 not available - R2 storage operations will fail")
            return
        
        # Initialize R2 client
        try:
            self.client = boto3.client(
                's3',
                endpoint_url=config.endpoint_url,
                aws_access_key_id=config.access_key_id,
                aws_secret_access_key=config.secret_access_key,
                region_name=config.region  # Usually 'auto' for R2
            )
            self.logger.info("R2 client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize R2 client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if R2 storage is available and properly configured."""
        return HAS_BOTO3 and self.client is not None
    
    async def test_connection(self) -> bool:
        """Test connection to R2 storage."""
        if not self.is_available():
            return False
        
        try:
            # Try to list objects (limit to 1 for quick test)
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.list_objects_v2(
                    Bucket=self.config.bucket_name,
                    MaxKeys=1
                )
            )
            self.logger.info("R2 connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"R2 connection test failed: {e}")
            return False
    
    def _generate_pdf_key(self, article_info: Dict[str, Any]) -> str:
        """Generate a unique key for storing PDF in R2."""
        # Use DOI, PMID, or title to create a unique identifier
        identifier_parts = []
        
        if article_info.get('doi'):
            # Clean DOI for filename
            doi = str(article_info['doi']).replace('/', '_').replace(':', '_')
            identifier_parts.append(f"doi_{doi}")
        
        if article_info.get('pmid'):
            identifier_parts.append(f"pmid_{article_info['pmid']}")
        
        if article_info.get('title'):
            # Create hash of title for uniqueness
            title_hash = hashlib.md5(article_info['title'].encode()).hexdigest()[:8]
            identifier_parts.append(f"title_{title_hash}")
        
        if article_info.get('id'):
            identifier_parts.append(f"id_{article_info['id']}")
        
        # Fallback to timestamp if no identifiers
        if not identifier_parts:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')[:-3]
            identifier_parts.append(f"unknown_{timestamp}")
        
        # Create the key
        base_name = "_".join(identifier_parts[:2])  # Use max 2 parts to keep filename reasonable
        key = f"{self.config.pdf_prefix}{base_name}.pdf"
        
        return key
    
    async def store_pdf(
        self, 
        pdf_content: bytes, 
        article_info: Dict[str, Any],
        overwrite: bool = False
    ) -> Optional[str]:
        """
        Store PDF content in R2 storage.
        
        Args:
            pdf_content: PDF file content as bytes
            article_info: Article metadata for generating storage key
            overwrite: Whether to overwrite existing files
            
        Returns:
            Storage key if successful, None otherwise
        """
        if not self.is_available():
            self.logger.error("R2 storage not available")
            return None
        
        try:
            key = self._generate_pdf_key(article_info)
            
            # Check if file already exists
            if not overwrite:
                if await self._key_exists(key):
                    self.logger.info(f"PDF already exists in R2: {key}")
                    return key
            
            # Prepare metadata
            metadata = {
                'Content-Type': 'application/pdf',
                'article-title': str(article_info.get('title', ''))[:256],  # Limit metadata size
                'article-doi': str(article_info.get('doi', ''))[:256],
                'article-pmid': str(article_info.get('pmid', ''))[:64],
                'upload-timestamp': datetime.now(timezone.utc).isoformat(),
                'content-size': str(len(pdf_content))
            }
            
            # Remove empty metadata
            metadata = {k: v for k, v in metadata.items() if v}
            
            # Upload to R2
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.put_object(
                    Bucket=self.config.bucket_name,
                    Key=key,
                    Body=pdf_content,
                    ContentType='application/pdf',
                    Metadata=metadata
                )
            )
            
            self.logger.info(f"Successfully stored PDF in R2: {key} ({len(pdf_content)} bytes)")
            return key
            
        except Exception as e:
            self.logger.error(f"Error storing PDF in R2: {e}")
            return None
    
    async def retrieve_pdf(self, key: str) -> Optional[bytes]:
        """
        Retrieve PDF content from R2 storage.
        
        Args:
            key: Storage key for the PDF
            
        Returns:
            PDF content as bytes, or None if not found
        """
        if not self.is_available():
            self.logger.error("R2 storage not available")
            return None
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.get_object(
                    Bucket=self.config.bucket_name,
                    Key=key
                )
            )
            
            pdf_content = response['Body'].read()
            self.logger.info(f"Successfully retrieved PDF from R2: {key} ({len(pdf_content)} bytes)")
            return pdf_content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.warning(f"PDF not found in R2: {key}")
            else:
                self.logger.error(f"Error retrieving PDF from R2: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error retrieving PDF from R2: {e}")
            return None
    
    async def _key_exists(self, key: str) -> bool:
        """Check if a key exists in R2 storage."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.head_object(
                    Bucket=self.config.bucket_name,
                    Key=key
                )
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                raise
    
    async def delete_pdf(self, key: str) -> bool:
        """
        Delete PDF from R2 storage.
        
        Args:
            key: Storage key for the PDF
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.is_available():
            self.logger.error("R2 storage not available")
            return False
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.delete_object(
                    Bucket=self.config.bucket_name,
                    Key=key
                )
            )
            
            self.logger.info(f"Successfully deleted PDF from R2: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting PDF from R2: {e}")
            return False
    
    async def list_pdfs(self, prefix: Optional[str] = None, max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List PDFs in R2 storage.
        
        Args:
            prefix: Optional prefix to filter results
            max_keys: Maximum number of keys to return
            
        Returns:
            List of PDF information dictionaries
        """
        if not self.is_available():
            self.logger.error("R2 storage not available")
            return []
        
        try:
            list_prefix = prefix or self.config.pdf_prefix
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.list_objects_v2(
                    Bucket=self.config.bucket_name,
                    Prefix=list_prefix,
                    MaxKeys=max_keys
                )
            )
            
            pdfs = []
            for obj in response.get('Contents', []):
                pdfs.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag']
                })
            
            self.logger.info(f"Found {len(pdfs)} PDFs in R2 with prefix: {list_prefix}")
            return pdfs
            
        except Exception as e:
            self.logger.error(f"Error listing PDFs from R2: {e}")
            return []
    
    async def get_pdf_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get metadata for a PDF stored in R2.
        
        Args:
            key: Storage key for the PDF
            
        Returns:
            Metadata dictionary
        """
        if not self.is_available():
            return {}
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.head_object(
                    Bucket=self.config.bucket_name,
                    Key=key
                )
            )
            
            metadata = response.get('Metadata', {})
            metadata.update({
                'content_length': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"')
            })
            
            return metadata
            
        except Exception as e:
            self.logger.warning(f"Could not get metadata for {key}: {e}")
            return {}
    
    def get_pdf_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for accessing a PDF.
        
        Args:
            key: Storage key for the PDF
            expires_in: URL expiration time in seconds
            
        Returns:
            Presigned URL or None if generation fails
        """
        if not self.is_available():
            return None
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.config.bucket_name,
                    'Key': key
                },
                ExpiresIn=expires_in
            )
            
            self.logger.debug(f"Generated presigned URL for {key} (expires in {expires_in}s)")
            return url
            
        except Exception as e:
            self.logger.error(f"Error generating presigned URL for {key}: {e}")
            return None
    
    async def cleanup_old_pdfs(self, days_old: int = 30) -> int:
        """
        Clean up PDFs older than specified days.
        
        Args:
            days_old: Delete PDFs older than this many days
            
        Returns:
            Number of PDFs deleted
        """
        if not self.is_available():
            return 0
        
        try:
            from datetime import timedelta
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            pdfs = await self.list_pdfs()
            old_pdfs = [
                pdf for pdf in pdfs 
                if pdf['last_modified'].replace(tzinfo=timezone.utc) < cutoff_date
            ]
            
            deleted_count = 0
            for pdf in old_pdfs:
                if await self.delete_pdf(pdf['key']):
                    deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} old PDFs (older than {days_old} days)")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error during PDF cleanup: {e}")
            return 0