# Google API Setup Guide

## Step-by-Step Instructions

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a project" → "New Project"
3. Enter project name: "Systematic Review Tool"
4. Click "Create"

### 2. Enable Required APIs

1. In the Google Cloud Console, go to "APIs & Services" → "Library"
2. Search and enable these APIs:
   - **Google Sheets API**
   - **Google Drive API**

### 3. Create Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. If prompted, configure OAuth consent screen:
   - Choose "External" user type
   - Fill in app name: "Systematic Review Data Extraction"
   - Add your email as user and developer email
   - Add scopes: `../auth/spreadsheets` and `../auth/drive.readonly`
4. For Application type, choose "Desktop application"
5. Name it "Systematic Review Desktop Client"
6. Click "Create"

### 4. Download Credentials

1. Click the download icon next to your newly created OAuth 2.0 Client ID
2. Save the file as `credentials.json` in your project root directory

### 5. Test Authentication

```bash
# Run the test script
python test_setup.py
```

On first run, it will:
- Open your web browser
- Ask you to sign in to Google
- Request permission to access your sheets
- Create a `token.json` file for future use

## Security Notes

- Keep `credentials.json` and `token.json` private
- Add them to `.gitignore`
- The token will auto-refresh when it expires

## Troubleshooting

### "Access blocked" error
- Make sure your app is verified or add test users in OAuth consent screen

### "Invalid credentials" error
- Re-download `credentials.json`
- Delete `token.json` and re-authenticate

### "Insufficient permissions" error
- Ensure the Google account has access to the spreadsheet
- Check that APIs are enabled in Google Cloud Console
