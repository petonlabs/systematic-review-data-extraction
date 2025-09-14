#!/usr/bin/env python3
"""
Quick demonstration of the enhanced systematic review extraction tool.
This script shows the available options without running the full extraction.
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.extraction_mode_manager import ExtractionModeManager, ExtractionMethod


def show_configuration_status():
    """Show current configuration status."""
    print("🔧 CONFIGURATION STATUS")
    print("="*60)
    
    config = Config()
    
    # Check Azure OpenAI
    azure_configured = all([
        config.azure_config.get('endpoint'),
        config.azure_config.get('key'),
        config.azure_config.get('deployment')
    ])
    
    if azure_configured:
        print("✅ Azure OpenAI: Configured")
    else:
        print("❌ Azure OpenAI: Not configured")
        print("   Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_DEPLOYMENT")
    
    # Check R2 configuration
    r2_configured = config.validate_r2_config()
    if r2_configured:
        print("✅ Cloudflare R2: Configured")
    else:
        print("❌ Cloudflare R2: Not configured")
        print("   Required for PDF storage: R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME")
    
    # Check Google Sheets
    sheets_configured = Path(config.sheets_config.credentials_file).exists()
    if sheets_configured:
        print("✅ Google Sheets: Credentials file found")
    else:
        print("❌ Google Sheets: credentials.json not found")
    
    print()


def show_extraction_methods():
    """Show available extraction methods."""
    print("📋 EXTRACTION METHODS")
    print("="*60)
    
    print("1. Web-based Extraction (Original)")
    print("   • Fetches articles directly from web sources")
    print("   • Uses DOI resolution, Unpaywall, CrossRef, PMC")
    print("   • Faster for immediately accessible content")
    print("   • No additional storage requirements")
    print("   • ✅ Always available")
    
    print("\n2. PDF-based Extraction (New)")
    print("   • Downloads PDFs from multiple sources")  
    print("   • Stores PDFs in Cloudflare R2 for archival")
    print("   • Extracts text using memory-efficient processing")
    print("   • Better for systematic collection and offline processing")
    
    config = Config()
    mode_manager = ExtractionModeManager(config)
    pdf_available = mode_manager.is_pdf_method_available()
    
    if pdf_available:
        print("   • ✅ Available (PDF processing + R2 configured)")
    else:
        print("   • ❌ Not available (missing dependencies or R2 config)")
    
    print()


def show_current_state():
    """Show current extraction state if any."""
    print("📊 CURRENT STATE")
    print("="*60)
    
    try:
        config = Config()
        mode_manager = ExtractionModeManager(config)
        
        summary = mode_manager.get_progress_summary()
        
        if summary['method'] == 'none':
            print("No previous extraction found")
        else:
            print(f"Last method used: {summary['method']}")
            print(f"Last used: {summary['last_used']}")
            print(f"Total processed: {summary['total_processed']}")
            print(f"Success rate: {summary['success_rate']:.1f}%")
            
            if summary['resume_from']:
                print(f"Can resume from: {summary['resume_from']}")
            else:
                print("Previous run completed")
    
    except Exception as e:
        print(f"Error reading state: {e}")
    
    print()


def show_next_steps():
    """Show recommended next steps."""
    print("🚀 NEXT STEPS")
    print("="*60)
    
    config = Config()
    
    # Check what's missing
    azure_configured = all([
        config.azure_config.get('endpoint'),
        config.azure_config.get('key'),
        config.azure_config.get('deployment')
    ])
    
    r2_configured = config.validate_r2_config()
    sheets_configured = Path(config.sheets_config.credentials_file).exists()
    
    if not azure_configured:
        print("1. 🔧 Configure Azure OpenAI in .env file:")
        print("   cp .env.template .env")
        print("   # Edit .env with your Azure OpenAI credentials")
    
    if not sheets_configured:
        print("2. 🔧 Set up Google Sheets credentials:")
        print("   # Download credentials.json from Google Cloud Console")
        print("   # Place in project root directory")
    
    if not r2_configured:
        print("3. 🔧 Optional: Configure Cloudflare R2 for PDF storage:")
        print("   # Add R2 credentials to .env file")
        print("   # Required for PDF-based extraction method")
    
    print("\n4. 🧪 Test the configuration:")
    print("   python3 tests/test_enhanced_functionality.py")
    
    print("\n5. 🚀 Run the enhanced extraction tool:")
    print("   python3 enhanced_main.py")
    
    if azure_configured and sheets_configured:
        print("\n✅ You're ready to start extraction!")
    else:
        print("\n⚠️  Complete configuration steps above before starting")


def main():
    """Main demo function."""
    print("🎯 SYSTEMATIC REVIEW DATA EXTRACTION TOOL")
    print("Enhanced with PDF-based extraction capabilities")
    print("="*60)
    print()
    
    show_configuration_status()
    show_extraction_methods()
    show_current_state()
    show_next_steps()
    
    print("\n" + "="*60)
    print("📖 For detailed documentation, see README.md")
    print("🐛 For issues, check the logs/ directory")
    print("💡 Run 'python3 enhanced_main.py' to start extraction")


if __name__ == "__main__":
    main()