# Execution Scripts

Main scripts for running the systematic review data extraction system.

## Scripts

### Main Execution
- **`run_extraction.py`** - Main extraction script for processing articles  
- **`restart_extraction.py`** - Restart script with resilient fallback strategies for failed articles
- **`run_with_spreadsheet.py`** - Configurable script for different spreadsheets

### Enhanced Extraction
- **`enhanced_main.py`** - Enhanced extraction with PDF and web-based methods
- **`demo_enhanced.py`** - Demonstration of enhanced extraction capabilities

## Usage

All scripts can be run from the project root using convenience wrappers:

```bash
# Main extraction
python3 run_extraction.py

# Restart failed articles with fallback strategies
python3 restart_extraction.py

# Run with specific spreadsheet
python3 run_with_spreadsheet.py --spreadsheet-id YOUR_SHEET_ID

# Enhanced extraction with PDF support
python3 src/scripts/enhanced_main.py
```

## Configuration

Scripts use configuration from:
- `.env` file for API credentials
- `src/config.py` for system configuration
- Command line arguments for runtime options

## Monitoring

All scripts create logs in the `logs/` directory and update progress in `progress.db`.
