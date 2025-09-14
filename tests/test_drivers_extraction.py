#!/usr/bin/env python3
"""
Quick test to verify that drivers data is being extracted and written to sheets.
"""

import asyncio
import sys
import os
from pathlib import Path
import dspy

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.data_extractor import DataExtractor


async def test_drivers_extraction():
    """Test that drivers data is being extracted."""
    print("🧪 Testing Drivers, Innovations & Policy Context extraction...")
    
    try:
        config = Config()
        
        # Configure DSPy with Azure OpenAI
        lm = dspy.LM(
            model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
            api_key=os.getenv('AZURE_OPENAI_KEY'),
            api_base=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            temperature=1.0,
            max_tokens=16000
        )
        dspy.configure(lm=lm)
        
        extractor = DataExtractor(config)
        
        # Test with a sample text about AMR and interventions
        sample_text = """
        This study examines surgical site infections in low-resource settings. 
        The main drivers of antimicrobial resistance identified include overuse of broad-spectrum antibiotics, 
        poor infection control practices, and lack of diagnostic capacity. 
        The authors propose several innovations including a bundle approach combining 
        preoperative antibiotic prophylaxis with enhanced surveillance. 
        Key gaps identified by the authors include insufficient laboratory capacity 
        and lack of antimicrobial stewardship programs. 
        Policy responses needed include implementation of national stewardship guidelines 
        and investment in diagnostic infrastructure.
        """
        
        extracted_data = await extractor.extract_all_data(sample_text)
        
        if 'drivers' in extracted_data:
            drivers_data = extracted_data['drivers']
            print("✅ Drivers data extracted successfully!")
            print("\n📋 Extracted Drivers Data:")
            for key, value in drivers_data.items():
                print(f"   {key}: {value}")
            print(f"\n🎯 Data will be written to sheet: 'Drivers, Innovations & Policy Context'")
            return True
        else:
            print("❌ No drivers data found in extracted data")
            print("Available keys:", list(extracted_data.keys()))
            return False
            
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_drivers_extraction())
    if success:
        print("\n✅ Test passed! Drivers extraction should now work in main extraction.")
    else:
        print("\n❌ Test failed. Check the logs for details.")
