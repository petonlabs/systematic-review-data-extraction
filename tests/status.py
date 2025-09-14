#!/usr/bin/env python3
"""
Project overview and status script.
"""

import sys
from pathlib import Path

def check_file_status():
    """Check the status of important files."""
    files_to_check = {
        '.env': 'Environment variables (Azure OpenAI config)',
        'credentials.json': 'Google API credentials',
        'token.json': 'Google API token (created after first auth)',
        'progress.db': 'Progress tracking database',
        'logs/': 'Log files directory',
        'src/': 'Source code directory',
    }
    
    print("📁 File Status Check:")
    print("-" * 30)
    
    for file_path, description in files_to_check.items():
        path = Path(file_path)
        if path.exists():
            if path.is_file():
                size = path.stat().st_size
                status = f"✅ {description} ({size} bytes)"
            else:
                contents = list(path.iterdir()) if path.is_dir() else []
                status = f"✅ {description} ({len(contents)} items)"
        else:
            if file_path == 'token.json':
                status = f"⏳ {description} (created on first run)"
            elif file_path == 'credentials.json':
                status = f"❌ {description} (REQUIRED - see GOOGLE_SETUP.md)"
            else:
                status = f"⏳ {description} (created when needed)"
        
        print(f"  {status}")

def show_next_steps():
    """Show next steps based on current status."""
    print("\n🚀 Getting Started:")
    print("-" * 30)
    
    has_creds = Path('credentials.json').exists()
    has_env = Path('.env').exists()
    
    if not has_env:
        print("1. ❌ Set up .env file with Azure OpenAI credentials")
    else:
        print("1. ✅ Azure OpenAI configured")
    
    if not has_creds:
        print("2. ❌ Set up Google Sheets credentials")
        print("   → Run: python setup_credentials.py")
        print("   → Or follow GOOGLE_SETUP.md")
    else:
        print("2. ✅ Google credentials ready")
        print("   → Run: python tests/test_setup.py (to verify connection)")
    
    print("\n3. 🎯 Test the system:")
    print("   → python demo.py (test data extraction)")
    print("   → python tests/test_setup.py (test full setup)")
    
    print("\n4. 🚀 Start extraction:")
    print("   → python main.py (process all articles)")
    
    print("\n📊 Monitor progress:")
    print("   → Check logs/ directory for detailed logs")
    print("   → Query progress.db for processing status")

def show_project_summary():
    """Show project summary."""
    print("🧬 Systematic Review Data Extraction Tool")
    print("="*50)
    print()
    print("Purpose: Automate data extraction from research articles")
    print("Method:  DSPy + Azure OpenAI + Google Sheets integration")
    print("Target:  36 research articles from your systematic review")
    print()
    print("📋 What this tool extracts:")
    print("  • Study characteristics (design, setting, duration)")
    print("  • Population characteristics (age, gender, conditions)")
    print("  • Interventions and comparators")
    print("  • Primary outcomes (SSI epidemiology, AMR patterns)")
    print("  • Secondary outcomes (clinical/economic impact)")
    print("  • Drivers, innovations, policy context")
    print()
    print("📈 Features:")
    print("  • Fetches full-text articles from DOIs/PMIDs")
    print("  • Context-aware chunking for long articles")
    print("  • Rate limiting for API calls")
    print("  • Progress tracking and resumption")
    print("  • Comprehensive logging")
    print()

def main():
    """Main function."""
    show_project_summary()
    check_file_status()
    show_next_steps()
    
    print("\n📚 Documentation:")
    print("  • README.md - Complete setup and usage guide")
    print("  • GOOGLE_SETUP.md - Google API setup instructions")
    print("  • demo.py - Test extraction with sample data")
    print("  • tests/test_setup.py - Verify all components")
    
    print("\n🆘 Need help?")
    print("  • Check the logs/ directory for error details")
    print("  • Review the README.md troubleshooting section")
    print("  • Ensure all API credentials are valid")

if __name__ == "__main__":
    main()
