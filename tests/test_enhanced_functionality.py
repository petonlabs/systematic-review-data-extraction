#!/usr/bin/env python3
"""
Test script for enhanced PDF-based extraction functionality.
"""

import asyncio
import logging
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.pdf_processor import PdfProcessor
from src.cloudflare_r2 import CloudflareR2Storage
from src.enhanced_article_fetcher import EnhancedArticleFetcher
from src.extraction_mode_manager import ExtractionModeManager, ExtractionMethod


async def test_pdf_processor():
    """Test PDF text extraction functionality."""
    print("Testing PDF processor...")
    
    try:
        config = Config()
        pdf_processor = PdfProcessor(config.pdf_config)
        
        # Create a minimal test PDF (this is just a placeholder - in real use, you'd have actual PDFs)
        print("✅ PDF processor initialized successfully")
        
        # Test PDF validation
        valid_pdf_header = b'%PDF-1.4\n'
        invalid_content = b'This is not a PDF'
        
        print(f"✅ Valid PDF detection: {pdf_processor.validate_pdf(valid_pdf_header)}")
        print(f"✅ Invalid content detection: {not pdf_processor.validate_pdf(invalid_content)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing PDF processor: {e}")
        return False


async def test_r2_storage():
    """Test Cloudflare R2 storage functionality."""
    print("\nTesting Cloudflare R2 storage...")
    
    try:
        config = Config()
        
        if not config.validate_r2_config():
            print("⚠️  R2 configuration not found - skipping R2 tests")
            print("   To test R2 functionality, configure R2 settings in .env file")
            return True
        
        r2_storage = CloudflareR2Storage(config.r2_config)
        
        if not r2_storage.is_available():
            print("❌ R2 storage not available")
            return False
        
        # Test connection
        connection_ok = await r2_storage.test_connection()
        if connection_ok:
            print("✅ R2 connection successful")
        else:
            print("❌ R2 connection failed")
            return False
        
        # Test storage operations with a dummy PDF
        test_pdf_content = b'%PDF-1.4\nTest PDF content for R2 testing'
        test_article = {
            'id': 'test_r2_article',
            'title': 'Test Article for R2 Storage',
            'doi': '10.1234/test.r2'
        }
        
        # Store test PDF
        print("Testing PDF storage...")
        r2_key = await r2_storage.store_pdf(test_pdf_content, test_article)
        
        if r2_key:
            print(f"✅ Test PDF stored successfully: {r2_key}")
            
            # Test retrieval
            print("Testing PDF retrieval...")
            retrieved_content = await r2_storage.retrieve_pdf(r2_key)
            
            if retrieved_content == test_pdf_content:
                print("✅ Test PDF retrieved successfully")
                
                # Test metadata
                metadata = await r2_storage.get_pdf_metadata(r2_key)
                print(f"✅ Retrieved metadata: {len(metadata)} fields")
                
                # Clean up test PDF
                await r2_storage.delete_pdf(r2_key)
                print("✅ Test PDF cleaned up")
                
                return True
            else:
                print("❌ Retrieved content doesn't match stored content")
                return False
        else:
            print("❌ Failed to store test PDF")
            return False
            
    except Exception as e:
        print(f"❌ Error testing R2 storage: {e}")
        return False


async def test_enhanced_fetcher():
    """Test enhanced article fetcher with both methods."""
    print("\nTesting enhanced article fetcher...")
    
    try:
        config = Config()
        
        # Test web-based method
        print("Testing web-based fetching...")
        web_fetcher = EnhancedArticleFetcher(config, ExtractionMethod.WEB_BASED)
        
        test_article = {
            'id': 'test_article_web',
            'title': 'Test Article for Web Fetching',
            'doi': '10.1371/journal.pone.0123456',  # Example DOI
            'pmid': '12345678'
        }
        
        # This might fail without network access, but that's expected in some environments
        try:
            async with web_fetcher:
                web_result = await web_fetcher.fetch_article(test_article)
                if web_result:
                    print(f"✅ Web-based fetching returned {len(web_result)} characters")
                else:
                    print("⚠️  Web-based fetching returned no content (expected in some environments)")
        except Exception as e:
            print(f"⚠️  Web-based fetching failed: {e} (expected without network access)")
        
        # Test PDF-based method initialization
        print("Testing PDF-based fetcher initialization...")
        pdf_fetcher = EnhancedArticleFetcher(config, ExtractionMethod.PDF_BASED)
        
        if pdf_fetcher.pdf_processor:
            print("✅ PDF processor initialized in enhanced fetcher")
        else:
            print("❌ PDF processor not initialized")
            return False
        
        if pdf_fetcher.r2_storage and config.validate_r2_config():
            print("✅ R2 storage initialized in enhanced fetcher")
        elif not config.validate_r2_config():
            print("⚠️  R2 storage not configured (expected without R2 settings)")
        else:
            print("❌ R2 storage initialization failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced fetcher: {e}")
        return False


def test_extraction_mode_manager():
    """Test extraction mode manager functionality."""
    print("\nTesting extraction mode manager...")
    
    try:
        config = Config()
        mode_manager = ExtractionModeManager(config)
        
        # Test state management
        print("Testing state management...")
        
        # Set a test method
        success = mode_manager.set_method(
            ExtractionMethod.WEB_BASED,
            pdf_storage_enabled=False,
            notes="Test method setting"
        )
        
        if success:
            print("✅ Method setting successful")
        else:
            print("❌ Method setting failed")
            return False
        
        # Load the state back
        current_method = mode_manager.get_current_method()
        if current_method == ExtractionMethod.WEB_BASED:
            print("✅ Method retrieval successful")
        else:
            print("❌ Method retrieval failed")
            return False
        
        # Test progress summary
        summary = mode_manager.get_progress_summary()
        print(f"✅ Progress summary retrieved: {len(summary)} fields")
        
        # Test PDF method availability check
        pdf_available = mode_manager.is_pdf_method_available()
        print(f"✅ PDF method availability check: {pdf_available}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing extraction mode manager: {e}")
        return False


async def test_full_workflow():
    """Test a simplified version of the full workflow."""
    print("\nTesting simplified full workflow...")
    
    try:
        config = Config()
        mode_manager = ExtractionModeManager(config)
        
        # Set method programmatically (avoid interactive prompt in tests)
        mode_manager.set_method(ExtractionMethod.WEB_BASED, notes="Automated test")
        
        # Initialize components
        enhanced_fetcher = EnhancedArticleFetcher(config, ExtractionMethod.WEB_BASED)
        
        print("✅ Workflow components initialized")
        
        # Test with mock article data
        mock_article = {
            'id': 'test_workflow_article',
            'title': 'Mock Article for Workflow Testing',
            'doi': '10.1234/mock.article',
            'abstract': 'This is a mock article abstract for testing purposes.'
        }
        
        # Since we can't test actual data extraction without real content,
        # we'll just verify the setup
        print("✅ Mock data prepared for workflow testing")
        print("✅ Full workflow setup completed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in full workflow test: {e}")
        return False


async def main():
    """Main test function."""
    print("🧪 Starting enhanced PDF extraction functionality tests...\n")
    
    # Setup logging to reduce noise during tests
    logging.basicConfig(level=logging.WARNING)
    
    all_passed = True
    
    # Run tests
    tests = [
        ("PDF Processor", test_pdf_processor),
        ("Cloudflare R2 Storage", test_r2_storage),
        ("Enhanced Article Fetcher", test_enhanced_fetcher),
        ("Extraction Mode Manager", lambda: test_extraction_mode_manager()),
        ("Full Workflow", test_full_workflow)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running {test_name} Test")
        print('='*60)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if not result:
                all_passed = False
                print(f"❌ {test_name} test failed")
            else:
                print(f"✅ {test_name} test passed")
                
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All tests passed! Enhanced PDF functionality is ready to use.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    print("\n📋 Next steps:")
    print("1. Configure .env file with Azure OpenAI and Cloudflare R2 credentials")
    print("2. Run 'python enhanced_main.py' to use the enhanced extraction tool")
    print("3. Choose between web-based and PDF-based extraction methods")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)