#!/usr/bin/env python3
"""
Fixed OAuth setup guide for Google API
"""

print("""
🔧 GOOGLE API OAUTH SETUP - CORRECTED SCOPES

The error you encountered is because of incorrect OAuth scopes setup. 
Here's the corrected process:

📋 STEP 1: OAuth Consent Screen Configuration

1. Go to Google Cloud Console: https://console.cloud.google.com
2. Navigate to "APIs & Services" → "OAuth consent screen"
3. Choose "External" user type
4. Fill in the required fields:
   - App name: "Systematic Review Data Extraction"
   - User support email: your-email@domain.com
   - Developer contact information: your-email@domain.com

5. In the SCOPES section, click "Add or Remove Scopes"
6. Add these EXACT scopes (search for them):
   ✅ https://www.googleapis.com/auth/spreadsheets
   ✅ https://www.googleapis.com/auth/drive.readonly

   DO NOT USE:
   ❌ ../auth/spreadsheets (this was incorrect in the original guide)

7. In "Test users" section, add your email address as a test user

📋 STEP 2: Create OAuth 2.0 Client ID

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Application type: "Desktop application" 
4. Name: "Systematic Review Desktop Client"
5. Click "Create"
6. Download the JSON file and save as 'credentials.json'

📋 STEP 3: Test the Setup

Run this command to test:
    python tests/test_setup.py

If you still get access_denied errors:

1. Delete token.json if it exists: rm token.json
2. Make sure you're signed into Google with the email you added as test user
3. Try the authentication again

📋 STEP 4: Alternative - Use Service Account (Recommended for automation)

If OAuth keeps failing, you can use a Service Account instead:

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service account"
3. Name: "systematic-review-service"
4. Download the JSON key file as 'service-account.json'
5. Share your Google Sheet with the service account email
6. The system will automatically detect and use the service account

🚨 IMPORTANT: 
- Make sure the Google account you're using has access to the spreadsheet
- The spreadsheet must be shared with 'Editor' permissions for the account
- If using a service account, share the sheet with the service account email

🔄 NEXT STEPS:
1. Follow the corrected setup above
2. Run: python tests/test_setup.py
3. If successful, run: python demo.py to see data extraction in action

""")
