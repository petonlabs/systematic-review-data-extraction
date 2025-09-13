#!/usr/bin/env python3
"""
Google OAuth Setup Helper
Provides detailed guidance for fixing OAuth consent screen issues.
"""

print("🔧 Google OAuth 403 Error Fix Guide")
print("=" * 50)

print("\n❌ You're getting Error 403: access_denied")
print("This happens when the OAuth consent screen isn't properly configured.\n")

print("🔧 Quick Fix Steps:")
print("1. Go to Google Cloud Console: https://console.cloud.google.com")
print("2. Select your project")
print("3. Go to 'APIs & Services' → 'OAuth consent screen'")
print("4. Choose 'External' user type (unless you have Google Workspace)")
print("5. Fill in required fields:")
print("   - App name: 'Systematic Review Tool'")
print("   - User support email: your-email@gmail.com")
print("   - Developer contact: your-email@gmail.com")
print("6. Click 'Save and Continue'")
print("7. On 'Scopes' page, click 'Save and Continue' (no changes needed)")
print("8. On 'Test users' page:")
print("   - Click '+ ADD USERS'")
print("   - Add your Gmail address")
print("   - Click 'Save'")
print("9. Click 'Save and Continue' until done")

print("\n🔄 Alternative: Use Internal App (if you have Google Workspace)")
print("- Choose 'Internal' instead of 'External' on OAuth consent screen")
print("- This skips the verification process")

print("\n🧪 Test Again:")
print("After making these changes, run:")
print("   rm token.json  # Delete old token")
print("   python test_setup.py")

print("\n📧 Still having issues?")
print("Make sure you're using the same Google account that:")
print("- Has access to your Google Sheet")
print("- Is added as a test user in OAuth consent screen")
print("- Owns the Google Cloud project")

print("\n💡 Pro tip:")
print("The consent screen shows 'This app isn't verified' - that's normal for test apps.")
print("Click 'Advanced' → 'Go to Systematic Review Tool (unsafe)' to proceed.")
