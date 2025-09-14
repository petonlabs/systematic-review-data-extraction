#!/usr/bin/env python3
"""
Run systematic review data extraction with configurable spreadsheet ID.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
from src.config import Config

# Load environment variables
load_dotenv()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Run systematic review data extraction with configurable spreadsheet',
        epilog="""
Examples:
  run_with_spreadsheet.py --spreadsheet-id 12Sk9FomrPi49Ql-Th01NkN8vNMC9sgBEa5XWbIsb1Dw
  run_with_spreadsheet.py --spreadsheet-id 1ki0z_9QHBg4uUCe4HVN5Rx7Tp6kzeIrJCGsnQTZku_Q --enhanced
  run_with_spreadsheet.py --list-spreadsheets

Setup tests:
  python tests/test_setup.py          # Test all components
  python tests/test_r2_setup.py       # Test Cloudflare R2 setup specifically

Available spreadsheets:
  Original: 1ki0z_9QHBg4uUCe4HVN5Rx7Tp6kzeIrJCGsnQTZku_Q
  New:      12Sk9FomrPi49Ql-Th01NkN8vNMC9sgBEa5XWbIsb1Dw
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--spreadsheet-id', 
        type=str, 
        help='Google Sheets spreadsheet ID to process'
    )
    
    parser.add_argument(
        '--enhanced', 
        action='store_true', 
        help='Use enhanced extraction with PDF processing (requires Cloudflare R2 setup)'
    )
    
    parser.add_argument(
        '--list-spreadsheets', 
        action='store_true', 
        help='List known spreadsheet IDs and exit'
    )
    
    args = parser.parse_args()
    
    # Known spreadsheets
    spreadsheets = {
        "original": "1ki0z_9QHBg4uUCe4HVN5Rx7Tp6kzeIrJCGsnQTZku_Q",
        "new": "12Sk9FomrPi49Ql-Th01NkN8vNMC9sgBEa5XWbIsb1Dw"
    }
    
    if args.list_spreadsheets:
        print("\n🔗 Available Google Sheets:")
        for name, sheet_id in spreadsheets.items():
            url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
            print(f"  {name.title()}: {sheet_id}")
            print(f"    URL: {url}")
        print()
        return
    
    if not args.spreadsheet_id:
        print("❌ Error: Please provide a spreadsheet ID")
        print("Use --help for usage information or --list-spreadsheets to see available options")
        sys.exit(1)
    
    # Validate spreadsheet ID format (should be 44 characters)
    if len(args.spreadsheet_id) != 44:
        print(f"⚠️  Warning: Spreadsheet ID '{args.spreadsheet_id}' doesn't look like a valid Google Sheets ID")
        print("Expected format: 44 characters (letters, numbers, hyphens, underscores)")
    
    # Set environment variable for the script
    os.environ['GOOGLE_SHEETS_ID'] = args.spreadsheet_id
    
    print(f"🎯 Target spreadsheet: {args.spreadsheet_id}")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{args.spreadsheet_id}/edit"
    print(f"🔗 URL: {sheet_url}")
    
    try:
        # Test configuration
        config = Config(spreadsheet_id=args.spreadsheet_id)
        config.validate()
        
        print("✅ Configuration validated")
        print(f"📊 Spreadsheet ID: {config.sheets_config.spreadsheet_id}")
        
        if args.enhanced:
            print("🚀 Using enhanced extraction mode...")
            if not config.validate_r2_config():
                print("❌ Error: Enhanced mode requires Cloudflare R2 configuration")
                print("   Run 'python tests/test_r2_setup.py' to set up R2 storage")
                sys.exit(1)
            
            # Import and run enhanced version
            import enhanced_main
            enhanced_main.main_with_config(config)
        else:
            print("📋 Using standard extraction mode...")
            
            # Import and run standard version  
            import restart_extraction
            restart_extraction.main_with_config(config)
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
