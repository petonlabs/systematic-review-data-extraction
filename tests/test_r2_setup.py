#!/usr/bin/env python3
"""
Simple test script specifically for Cloudflare R2 storage setup verification.
Run this after configuring your R2 credentials to ensure everything works.
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

async def test_r2_functionality():
    """Comprehensive test of R2 storage functionality."""
    print("🔧 Testing Cloudflare R2 Storage Setup")
    print("=" * 50)
    
    try:
        # Import dependencies
        try:
            import importlib.util
            boto3_spec = importlib.util.find_spec('boto3')
            if boto3_spec is None:
                raise ImportError("boto3 not found")
            print("✅ boto3 library available")
        except ImportError:
            print("❌ boto3 library not found")
            print("   Run: uv add boto3")
            return False
        
        # Import our modules
        from src.config import Config
        from src.cloudflare_r2 import CloudflareR2Storage
        
        # Initialize config
        print("\n📋 Checking configuration...")
        config = Config()
        
        if not config.validate_r2_config():
            print("❌ R2 configuration incomplete")
            print_setup_guide()
            return False
        
        print("✅ R2 configuration found")
        print(f"   Endpoint: {config.r2_config.endpoint_url}")
        print(f"   Bucket: {config.r2_config.bucket_name}")
        
        # Initialize R2 client
        print("\n🔗 Testing R2 connection...")
        r2_storage = CloudflareR2Storage(config.r2_config)
        
        if not r2_storage.is_available():
            print("❌ R2 client not available")
            return False
        
        # Test connection
        connected = await r2_storage.test_connection()
        if not connected:
            print("❌ R2 connection failed")
            print("   Check your credentials and bucket name")
            return False
        
        print("✅ R2 connection successful!")
        
        # Test full workflow
        print("\n📄 Testing PDF storage workflow...")
        
        # Create test PDF content (minimal valid PDF)
        test_pdf = create_test_pdf()
        test_article = {
            'id': 'r2_test_001',
            'title': 'Test Article for R2 Setup Verification',
            'doi': '10.1234/r2.setup.test',
            'pmid': '88888888'
        }
        
        print("📤 Uploading test PDF...")
        r2_key = await r2_storage.store_pdf(test_pdf, test_article)
        
        if not r2_key:
            print("❌ PDF upload failed")
            return False
        
        print(f"✅ PDF uploaded successfully: {r2_key}")
        
        # Test download
        print("📥 Downloading test PDF...")
        downloaded = await r2_storage.retrieve_pdf(r2_key)
        
        if not downloaded or downloaded != test_pdf:
            print("❌ PDF download failed or content mismatch")
            return False
        
        print("✅ PDF downloaded and verified successfully")
        
        # Test metadata
        print("📊 Testing metadata...")
        metadata = await r2_storage.get_pdf_metadata(r2_key)
        
        if not metadata:
            print("⚠️  Could not retrieve metadata")
        else:
            print(f"✅ Metadata retrieved: {len(metadata)} fields")
            print(f"   Size: {metadata.get('content_length', 'unknown')} bytes")
        
        # Test presigned URL
        print("🔗 Testing presigned URL generation...")
        url = r2_storage.get_pdf_url(r2_key, expires_in=300)
        
        if not url:
            print("⚠️  Could not generate presigned URL")
        else:
            print("✅ Presigned URL generated successfully")
        
        # Test listing PDFs
        print("📋 Testing PDF listing...")
        pdfs = await r2_storage.list_pdfs(max_keys=5)
        
        if pdfs:
            print(f"✅ Found {len(pdfs)} PDFs in bucket")
        else:
            print("⚠️  No PDFs found (this might be expected)")
        
        # Cleanup
        print("🧹 Cleaning up test PDF...")
        deleted = await r2_storage.delete_pdf(r2_key)
        
        if deleted:
            print("✅ Test PDF deleted successfully")
        else:
            print("⚠️  Could not delete test PDF")
        
        print("\n" + "=" * 50)
        print("🎉 R2 SETUP TEST COMPLETED SUCCESSFULLY!")
        print("   Your Cloudflare R2 storage is ready for use.")
        print("   You can now use PDF-based extraction mode.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: uv add boto3")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def create_test_pdf():
    """Create a minimal valid PDF for testing."""
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(R2 Test PDF) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000110 00000 n 
0000000188 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
285
%%EOF"""


def print_setup_guide():
    """Print R2 setup instructions."""
    print("\n" + "=" * 60)
    print("📋 CLOUDFLARE R2 SETUP REQUIRED")
    print("=" * 60)
    
    print("\n🎯 To set up Cloudflare R2 for PDF storage:")
    print("\n1️⃣  Create R2 Account:")
    print("   • Visit: https://dash.cloudflare.com")
    print("   • Go to R2 Object Storage")
    print("   • Create a bucket (e.g., 'systematic-review-pdfs')")
    
    print("\n2️⃣  Get API Credentials:")
    print("   • Click 'Manage R2 API tokens'")
    print("   • Create token with R2 read/write permissions")
    print("   • Note: Account ID, Access Key, Secret Key")
    
    print("\n3️⃣  Update .env file:")
    print("   Add these lines to your .env file:")
    print("   ┌─────────────────────────────────────────────────┐")
    print("   │ R2_ENDPOINT_URL=https://ACCOUNT-ID.r2.cloudflare│")
    print("   │ R2_ACCESS_KEY_ID=your-access-key               │") 
    print("   │ R2_SECRET_ACCESS_KEY=your-secret-key           │")
    print("   │ R2_BUCKET_NAME=systematic-review-pdfs          │")
    print("   └─────────────────────────────────────────────────┘")
    
    print("\n4️⃣  Install Dependencies:")
    print("   Run: uv add boto3")
    
    print("\n5️⃣  Re-run Test:")
    print("   Run: python tests/test_r2_setup.py")
    
    print("\n💡 Benefits:")
    print("   • Direct PDF processing from research articles")
    print("   • Better text extraction accuracy")
    print("   • Archive PDFs for future reference")
    print("   • Cost-effective storage with no egress fees")
    print("=" * 60)


if __name__ == "__main__":
    print("🧪 Cloudflare R2 Setup Test")
    print("Testing R2 storage configuration and functionality...\n")
    
    try:
        success = asyncio.run(test_r2_functionality())
        
        if success:
            print("\n✅ SUCCESS: R2 storage is properly configured!")
            print("   You can now use enhanced PDF-based extraction.")
            sys.exit(0)
        else:
            print("\n❌ FAILED: R2 setup needs attention.")
            print("   Standard web-based extraction will still work.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
