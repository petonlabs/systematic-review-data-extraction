#!/usr/bin/env python3
"""
Add proper headers to the data extraction sheets.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import Config
from src.sheets_client import SheetsClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('AddHeaders')

# Define the proper headers for each sheet based on DSPy signatures
SHEET_HEADERS = {
    'Study Characteristics': [
        'Author',
        'Year of publication',
        'Title of paper',
        'Country/Countries',
        'Study Design',
        'Study Period',
        'Setting'
    ],
    'Population Characteristics': [
        'Total Sample Size (N)',
        'Population  Description',
        'Inclusion Criteria',
        'Exclusion Criteria',
        'Age (Mean/Median & SD/IQR)',
        'Sex Distribution',
        'Comorbidities',
        'Surgery Type'
    ],
    'Interventions & Comparators': [
        'Intervention Group (N)',
        'Intervention Details',
        'Comparator Group (N)',
        'Comparator Details',
        'Adherence to Guidelines (%)'
    ],
    'Primary Outcomes (SSI Epidemiology & AMR)': [
        'Total Procedures',
        'Total SSIs',
        'SSI Incidence Rate',
        'Method of SSI Diagnosis',
        'Total SSI Isolates',
        'Pathogen 1 Name (Name of the most common isolated pathogen)',
        'Pathogen 1 Resistance (List antibiotic resistance)',
        'Pathogen 2 Name (Name of the 2nd most common pathogen)',
        'Pathogen 2 Resistance (List antibiotic resistance %)',
        'Resistance to WHO Critical Abx (Any specific data on resistance to WHO critical important antibiotics)'
    ],
    'Secondary Outcomes (Clinical & Economic Impact)': [
        'Morbidity - Additional Hospital Stay (days)',
        'Morbidity - Re-opertation rate (%)',
        'Morbidity - Readmission rate (%)',
        'Mortality - SSI attributable rate (%)',
        'Mortality - 30-day post-op',
        'Mortality - 90-day post-op (%)',
        'Hospital burden - Total length of stay (days)',
        'Economic - direct costs',
        'Economic - indirect costs'
    ],
    'Drivers, Innovations & Policy Context': [
        'Reported Drivers of AMR',
        'Interventions/Innovations Described',
        'Gaps Identified by Authors',
        'Policy Response/Capacity'
    ]
}

async def add_headers_to_sheets():
    """Add proper headers to data extraction sheets."""
    
    config = Config()
    sheets_client = SheetsClient(config.sheets_config)
    
    # Test connection
    if not await sheets_client.test_connection():
        logger.error("Connection failed")
        return
    
    logger.info("Adding headers to data extraction sheets...")
    
    for sheet_name, headers in SHEET_HEADERS.items():
        logger.info(f"\nProcessing {sheet_name}...")
        logger.info(f"Headers to add: {headers}")
        
        try:
            # Insert a new row at the top for headers
            logger.info("Inserting new row at top...")
            
            # Insert row request
            insert_request = {
                'requests': [{
                    'insertDimension': {
                        'range': {
                            'sheetId': None,  # We'll need to get this
                            'dimension': 'ROWS',
                            'startIndex': 0,
                            'endIndex': 1
                        },
                        'inheritFromBefore': False
                    }
                }]
            }
            
            # Get sheet metadata to find sheet ID
            metadata = sheets_client.service.spreadsheets().get(
                spreadsheetId=config.sheets_config.spreadsheet_id
            ).execute()
            
            sheet_id = None
            for sheet in metadata.get('sheets', []):
                if sheet.get('properties', {}).get('title') == sheet_name:
                    sheet_id = sheet.get('properties', {}).get('sheetId')
                    break
            
            if sheet_id is None:
                logger.error(f"Could not find sheet ID for {sheet_name}")
                continue
            
            insert_request['requests'][0]['insertDimension']['range']['sheetId'] = sheet_id
            
            # Execute insert row request
            sheets_client.service.spreadsheets().batchUpdate(
                spreadsheetId=config.sheets_config.spreadsheet_id,
                body=insert_request
            ).execute()
            
            logger.info("Row inserted, now adding headers...")
            
            # Add headers to the new first row
            range_name = f"{sheet_name}!A1:{chr(ord('A') + len(headers) - 1)}1"
            
            update_body = {
                'values': [headers]
            }
            
            sheets_client.service.spreadsheets().values().update(
                spreadsheetId=config.sheets_config.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=update_body
            ).execute()
            
            logger.info(f"✅ Headers added to {sheet_name}")
            
        except Exception as e:
            logger.error(f"❌ Error adding headers to {sheet_name}: {e}")
            continue
    
    logger.info("\n🎉 Headers added to all data extraction sheets!")
    logger.info("The sheets now have proper column headers that match the extracted data fields.")

if __name__ == "__main__":
    asyncio.run(add_headers_to_sheets())
