#!/usr/bin/env python3
"""
Test script to verify Google Sheets connection and basic functionality.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.sheets_client import SheetsClient
from src.progress_tracker import ProgressTracker


async def test_sheets_connection():
    """Test connection to Google Sheets."""
    print("Testing Google Sheets connection...")
    
    try:
        config = Config()
        sheets_client = SheetsClient(config.sheets_config)
        
        # Test connection
        connected = await sheets_client.test_connection()
        
        if connected:
            print("✅ Google Sheets connection successful!")
            
            # List all available sheet names first
            try:
                metadata = sheets_client.service.spreadsheets().get(
                    spreadsheetId=sheets_client.config.spreadsheet_id
                ).execute()
                
                sheets = metadata.get('sheets', [])
                print(f"\n📋 Available sheets in the spreadsheet:")
                for sheet in sheets:
                    title = sheet.get('properties', {}).get('title')
                    print(f"   - '{title}'")
                
            except Exception as e:
                print(f"   Error listing sheets: {e}")
            
            # Try to get articles
            try:
                articles = await sheets_client.get_articles()
                print(f"✅ Found {len(articles)} articles in the sheet")
                
                if articles:
                    print("\nSample article data:")
                    sample = articles[0]
                    for key, value in sample.items():
                        if value and key not in ['id', 'row_number']:
                            print(f"  {key}: {str(value)[:100]}...")
                            
            except Exception as e:
                print(f"❌ Error fetching articles: {e}")
                return False
            
            # Verify sheet structure alignment with EXACT sheet names
            sheet_structure = {
                'Study Characteristics': [
                    'Author', 'Year of publication', 'Title of paper', 'Country/Countries',
                    'Study Design', 'Study Period', 'Setting'
                ],
                'Population Characteristics': [
                    'Total Sample Size (N)', 'Population  Description', 'Inclusion Criteria',
                    'Exclusion Criteria', 'Age (Mean/Median & SD/IQR)', 'Sex (%Female)',
                    'Surgical Speciality ', 'Specific Procedures'  # Note the extra space in actual sheet
                ],
                'Interventions & Comparators': [
                    'Intervention Group (N)', 'Intervention Details', 'Comparator Group (N)',
                    'Comparator Details', 'Adherence to Guidelines (%)'
                ],
                'Primary Outcomes (SSI Epidemiology & AMR)': [
                    'Total Procedures', 'Total SSIs', 'SSI Incidence Rate',
                    'Method of SSI Diagnosis', 'Total SSI Isolates', 'Pathogen 1 Name',
                    'Pathogen 1 Resistance', 'Pathogen 2 Name', 'Pathogen 2 Resistance',
                    'Resistance to WHO Critical Abx'
                ],
                'Secondary Outcomes (Clinical & Economic Impact)': [
                    'Morbidity - Additional Hospital Stay', 'Morbidity - Re-operation rate',
                    'Morbidity - Readmission rate', 'Mortality - SSI attributable rate',
                    'Mortality - 30-day post-op', 'Mortality - 90-day post-op',
                    'Hospital burden - Total length of stay', 'Economic - direct costs',
                    'Economic - indirect costs'
                ],
                'Drivers, Innovations & Policy Context': [
                    'Reported Drivers of AMR', 'Interventions/Innovations Described',
                    'Gaps Identified by Authors', 'Policy Response/Capacity'
                ]
            }
            
            print("\n📋 Sheet Structure Verification:")
            print("=" * 60)
            
            alignment_issues = []
            for sheet_name, expected_columns in sheet_structure.items():
                try:
                    headers = await sheets_client.get_headers(sheet_name)
                    print(f"\n📊 Sheet: {sheet_name}")
                    print(f"   Expected columns: {len(expected_columns)}")
                    print(f"   Actual columns:   {len(headers)}")
                    
                    # Check alignment
                    missing_columns = set(expected_columns) - set(headers)
                    extra_columns = set(headers) - set(expected_columns)
                    
                    if not missing_columns and not extra_columns:
                        print("   ✅ Perfect alignment!")
                    else:
                        alignment_issues.append(sheet_name)
                        if missing_columns:
                            print(f"   ❌ Missing columns: {list(missing_columns)}")
                        if extra_columns:
                            print(f"   ⚠️  Extra columns: {list(extra_columns)}")
                    
                    # Show first few actual headers for verification
                    print(f"   📝 Headers (first 5): {headers[:5]}...")
                    
                except Exception as e:
                    print(f"   ❌ Error accessing sheet '{sheet_name}': {e}")
                    alignment_issues.append(sheet_name)
            
            print("\n" + "=" * 60)
            if not alignment_issues:
                print("🎉 ALL SHEETS PERFECTLY ALIGNED!")
            else:
                print(f"⚠️  {len(alignment_issues)} sheets need attention: {alignment_issues}")
                print("   Update signatures if column names don't match exactly")
        else:
            print("❌ Failed to connect to Google Sheets")
            return False
            
    except Exception as e:
        print(f"❌ Error during sheets test: {e}")
        return False
    
    return True


def test_progress_tracker():
    """Test progress tracking functionality."""
    print("\nTesting progress tracker...")
    
    try:
        config = Config()
        tracker = ProgressTracker(config.tracking_config)
        
        # Test basic operations
        test_article_id = "test_001"
        test_metadata = {
            'title': 'Test Article',
            'doi': '10.1234/test',
            'pmid': '12345'
        }
        
        # Start processing
        tracker.start_processing(test_article_id, test_metadata)
        print("✅ Started tracking test article")
        
        # Test success logging
        test_extracted_data = {
            'study_characteristics': {
                'study_type': 'RCT',
                'setting': 'Hospital'
            }
        }
        
        tracker.log_success(test_article_id, test_extracted_data)
        print("✅ Logged successful extraction")
        
        # Get progress summary
        summary = tracker.get_progress_summary()
        print(f"✅ Progress summary: {summary}")
        
        # Test export
        output_path = Path("test_export.csv")
        tracker.export_results(str(output_path), 'csv')
        
        if output_path.exists():
            print("✅ Export functionality working")
            output_path.unlink()  # Clean up
        else:
            print("❌ Export failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing progress tracker: {e}")
        return False


def test_dspy_configuration():
    """Test DSPy configuration with Azure OpenAI."""
    print("\nTesting DSPy configuration...")
    
    try:
        import dspy
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        # Configure Azure OpenAI LM with required settings for reasoning models
        lm = dspy.LM(
            model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
            api_key=os.getenv('AZURE_OPENAI_KEY'),
            api_base=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            temperature=1.0,  # Required for reasoning models
            max_tokens=16000  # Required minimum for reasoning models
        )
        dspy.configure(lm=lm)
        
        # Test simple prediction
        predict = dspy.Predict("question -> answer")
        response = predict(question="What is 2+2?")
        
        if hasattr(response, 'answer'):
            print(f"✅ DSPy working! Test response: {response.answer}")
            return True
        else:
            print("❌ DSPy response format unexpected")
            return False
            
    except Exception as e:
        print(f"❌ Error testing DSPy: {e}")
        return False


async def main():
    """Main test function."""
    print("🧪 Starting systematic review tool tests...\n")
    
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
    
    all_passed = True
    
    # Test 1: DSPy Configuration
    if not test_dspy_configuration():
        all_passed = False
    
    # Test 2: Progress Tracker
    if not test_progress_tracker():
        all_passed = False
    
    # Test 3: Google Sheets (may require authentication)
    try:
        if not await test_sheets_connection():
            all_passed = False
    except Exception as e:
        print(f"❌ Could not test sheets connection: {e}")
        print("   This might be normal if you haven't set up Google API credentials yet.")
        print("   See setup instructions below.")
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 All tests passed! The system is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    print("\n📋 Next steps:")
    print("1. Set up Google API credentials (credentials.json)")
    print("2. Run 'python main.py' to start the full extraction process")
    print("3. Monitor progress in logs/ directory and progress.db file")


if __name__ == "__main__":
    asyncio.run(main())
