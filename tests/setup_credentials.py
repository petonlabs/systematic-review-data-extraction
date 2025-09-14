#!/usr/bin/env python3
"""
Script to help set up Google Sheets credentials.
"""

import json
import sys
from pathlib import Path

def create_sample_credentials():
    """Create a sample credentials.json file for reference."""
    sample_creds = {
        "installed": {
            "client_id": "your_client_id.apps.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "your_client_secret",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open("credentials_sample.json", "w") as f:
        json.dump(sample_creds, f, indent=2)
    
    print("✅ Created credentials_sample.json")
    print("\n📋 Next steps:")
    print("1. Go to https://console.cloud.google.com")
    print("2. Create a new project or select existing one")
    print("3. Enable Google Sheets API and Google Drive API")
    print("4. Create OAuth 2.0 credentials for desktop application")
    print("5. Download the credentials file as 'credentials.json'")
    print("6. Place it in this directory")
    print("\nSee GOOGLE_SETUP.md for detailed instructions!")

def check_credentials():
    """Check if credentials exist and are valid format."""
    creds_path = Path("credentials.json")
    
    if not creds_path.exists():
        print("❌ credentials.json not found")
        return False
    
    try:
        with open(creds_path) as f:
            creds = json.load(f)
        
        required_keys = ["installed"]
        installed_keys = ["client_id", "client_secret", "auth_uri", "token_uri"]
        
        if not all(key in creds for key in required_keys):
            print("❌ Invalid credentials format - missing top-level keys")
            return False
        
        if not all(key in creds["installed"] for key in installed_keys):
            print("❌ Invalid credentials format - missing required fields")
            return False
        
        print("✅ credentials.json looks valid!")
        return True
        
    except json.JSONDecodeError:
        print("❌ credentials.json is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")
        return False

def main():
    """Main function."""
    print("🔐 Google Sheets Credentials Setup Helper")
    print("="*50)
    
    if check_credentials():
        print("\n✅ You're all set! Run 'python tests/test_setup.py' to test the connection.")
    else:
        print("\n❓ Would you like me to create a sample credentials file? (y/n): ", end="")
        response = input().lower().strip()
        
        if response in ['y', 'yes']:
            create_sample_credentials()
        else:
            print("📖 Please see GOOGLE_SETUP.md for setup instructions.")

if __name__ == "__main__":
    main()
