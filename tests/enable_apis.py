#!/usr/bin/env python3
"""
Quick API enabler guide for Google Cloud Console.
"""

def print_api_enabler_guide():
    """Print step-by-step guide to enable required APIs."""
    
    project_id = "278117637433"  # From your error message
    
    print("🔧 Google Cloud API Setup Required")
    print("=" * 50)
    print()
    print("Your OAuth authentication worked! Now you need to enable the APIs.")
    print()
    print("📋 Steps to follow:")
    print()
    print("1. Open this link in your browser:")
    print(f"   https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project={project_id}")
    print()
    print("2. Click the 'ENABLE' button for Google Sheets API")
    print()
    print("3. Then enable Google Drive API:")
    print(f"   https://console.developers.google.com/apis/api/drive.googleapis.com/overview?project={project_id}")
    print()
    print("4. Click the 'ENABLE' button for Google Drive API")
    print()
    print("5. Wait 2-3 minutes for the APIs to propagate")
    print()
    print("6. Run the test again:")
    print("   python test_setup.py")
    print()
    print("⚠️  Note: It may take a few minutes for the API changes to take effect.")
    print()
    print("🔗 Alternative - Direct links:")
    print("   • Google Cloud Console: https://console.cloud.google.com")
    print("   • APIs & Services > Library")
    print("   • Search for 'Google Sheets API' and enable it")
    print("   • Search for 'Google Drive API' and enable it")
    print()

if __name__ == "__main__":
    print_api_enabler_guide()
