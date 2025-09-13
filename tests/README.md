# Test Suite for Systematic Review Data Extraction

This directory contains all test files and utilities for the systematic review data extraction system.

## Test Files

### Core Tests
- **`test_setup.py`** - Main system verification test
  - Tests Google Sheets connection
  - Verifies sheet structure alignment  
  - Checks DSPy configuration
  - Tests progress tracking
  - **Usage**: `python tests/test_setup.py`

### Demo and Development Tests
- **`demo.py`** - Basic extraction demo
- **`full_demo.py`** - Complete end-to-end demo
- **`test_single_article.py`** - Test single article extraction
- **`test_url_handling.py`** - Test URL and DOI handling

### Setup Utilities
- **`enable_apis.py`** - Google API enablement helper
- **`fix_oauth.py`** - OAuth authentication fixer
- **`oauth_fix_guide.py`** - OAuth troubleshooting guide
- **`setup_credentials.py`** - Credential setup utility

## Quick Test Commands

```bash
# Run main system verification (recommended first test)
python tests/test_setup.py

# Test single article extraction
python tests/test_single_article.py

# Full system demo
python tests/full_demo.py

# Basic demo
python tests/demo.py
```

## Test Requirements

1. **Google Sheets Setup**:
   - `credentials.json` in root directory
   - Valid spreadsheet ID in config
   - Proper API permissions

2. **Environment**:
   - All dependencies installed via `uv`
   - `.env` file with API keys
   - DSPy configuration set up

## Expected Test Results

### ✅ Success Indicators
- Google Sheets connection successful
- Sheet structure alignment confirmed
- DSPy test responses working
- Progress tracking functional

### ❌ Common Issues
- **Sheet name mismatches**: Check exact sheet names in Google Sheets
- **API errors**: Verify credentials.json and API permissions
- **Import errors**: Ensure all dependencies installed

## Development Workflow

1. **First Run**: `python tests/test_setup.py`
2. **Fix Issues**: Address any failing tests
3. **Single Article Test**: `python tests/test_single_article.py`
4. **Full Extraction**: `python restart_extraction.py`

## Troubleshooting

If tests fail:
1. Check Google Sheets access permissions
2. Verify API credentials are valid
3. Ensure sheet names match exactly
4. Run `python tests/fix_oauth.py` for auth issues
