#!/usr/bin/env python3
"""
Demo script to show the extraction capabilities with sample text.
"""

import asyncio
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data_extractor import DataExtractor
from src.config import Config
import dspy
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Sample research article text (abbreviated for demo)
SAMPLE_ARTICLE = """
Title: Antimicrobial Resistance in Surgical Site Infections Following Colorectal Surgery: A Prospective Cohort Study

Abstract:
Background: Surgical site infections (SSIs) remain a significant complication following colorectal surgery, with increasing concerns about antimicrobial resistance (AMR) patterns. This study aimed to investigate the epidemiology of SSIs and characterize AMR patterns in a tertiary care hospital.

Methods: We conducted a prospective cohort study of 324 adult patients undergoing elective colorectal surgery at General Hospital from January 2022 to December 2023. Patients were followed for 30 days post-operatively for SSI development. Microbiological samples were collected from all SSIs and analyzed for pathogen identification and antimicrobial susceptibility testing.

Results: The overall SSI rate was 15.4% (50/324 patients). The most common pathogens isolated were Escherichia coli (32%), Enterococcus faecalis (24%), and Staphylococcus aureus (18%). High rates of resistance were observed: 45% of E. coli isolates were extended-spectrum beta-lactamase (ESBL) producers, 67% of Enterococcus isolates showed vancomycin resistance, and 23% of S. aureus were methicillin-resistant (MRSA).

Patients with SSIs had significantly longer hospital stays (median 12 days vs 5 days, p<0.001) and higher readmission rates (28% vs 8%, p<0.001). The additional cost per SSI patient was estimated at $8,450.

Risk factors associated with SSI included BMI >30 (OR 2.3, 95% CI 1.2-4.4), diabetes mellitus (OR 1.8, 95% CI 1.1-3.2), and prolonged operative time >180 minutes (OR 2.1, 95% CI 1.3-3.5).

Conclusions: SSIs following colorectal surgery show concerning patterns of antimicrobial resistance. Implementation of enhanced infection control measures and antimicrobial stewardship programs are urgently needed.

Study Design: Prospective cohort study
Setting: Tertiary care hospital, surgical department
Country: United States
Duration: 24 months (2022-2023)
Sample Size: 324 patients
Population: Adult patients undergoing elective colorectal surgery
Age Range: 18-85 years (mean 64.5 ± 12.3)
Gender: 52% female, 48% male
Inclusion Criteria: Elective colorectal surgery, age ≥18 years
Exclusion Criteria: Emergency surgery, immunocompromised patients, pregnancy
"""

async def demo_extraction():
    """Demonstrate the data extraction capabilities."""
    print("🧪 Systematic Review Data Extraction Demo")
    print("="*60)
    
    # Setup logging (suppress verbose logs for demo)
    logging.basicConfig(level=logging.WARNING)
    
    try:
        # Configure DSPy
        print("🔧 Configuring DSPy with Azure OpenAI...")
        lm = dspy.LM(
            model=f"azure/{os.getenv('AZURE_OPENAI_DEPLOYMENT')}",
            api_key=os.getenv('AZURE_OPENAI_KEY'),
            api_base=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            temperature=1.0,
            max_tokens=16000
        )
        dspy.configure(lm=lm)
        print("✅ DSPy configured successfully!")
        
        # Initialize data extractor
        config = Config()
        extractor = DataExtractor(config.extraction_config)
        
        print("\n📄 Sample Article Text:")
        print("-" * 40)
        print(SAMPLE_ARTICLE[:300] + "...\n")
        
        # Sample article metadata
        article_metadata = {
            'title': 'Antimicrobial Resistance in Surgical Site Infections Following Colorectal Surgery',
            'doi': '10.1234/demo.2024',
            'pmid': '12345678'
        }
        
        print("🔍 Extracting data using DSPy agents...")
        print("This may take a few moments...\n")
        
        # Extract all data
        extracted_data = await extractor.extract_all_data(SAMPLE_ARTICLE, article_metadata)
        
        if extracted_data:
            print("✅ Data extraction completed successfully!")
            print("\n📊 Extracted Data Summary:")
            print("=" * 60)
            
            for category, fields in extracted_data.items():
                print(f"\n🔹 {category.replace('_', ' ').title()}:")
                print("-" * 30)
                for field, value in fields.items():
                    if value and value.strip():
                        # Truncate long values for display
                        display_value = value[:100] + "..." if len(value) > 100 else value
                        print(f"  • {field}: {display_value}")
                    else:
                        print(f"  • {field}: [not found]")
        else:
            print("❌ No data was extracted. Check your configuration.")
        
        print("\n" + "="*60)
        print("🎉 Demo completed!")
        print("\n💡 This demonstrates how the tool will process your 36 research articles.")
        print("   Each article will be processed similarly, with results saved to Google Sheets.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("Please check your .env configuration and try again.")

async def main():
    """Main demo function."""
    await demo_extraction()

if __name__ == "__main__":
    asyncio.run(main())
