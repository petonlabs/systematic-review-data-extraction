# Debug Scripts

Collection of debugging and maintenance scripts for the systematic review data extraction system.

## Scripts

### Header Management
- **`add_headers.py`** - Add proper column headers to Google Sheets data extraction sheets
- **`check_headers.py`** - Verify headers match between sheets and extracted data fields

### Data Verification  
- **`check_articles.py`** - Check the structure and content of the articles sheet
- **`debug_sheets.py`** - Debug Google Sheets writing and data mapping issues
- **`debug_columns.py`** - Debug column alignment and mapping problems

## Usage

All scripts are designed to be run from the project root:

```bash
# Check current headers
python3 src/debug/check_headers.py

# Add missing headers
python3 src/debug/add_headers.py

# Debug sheets connection and data writing
python3 src/debug/debug_sheets.py
```

## Requirements

These scripts require:
- Google Sheets API credentials (`credentials.json`)
- Proper environment setup (`.env` file)
- Active database connection (`progress.db`)
