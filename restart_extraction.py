#!/usr/bin/env python3
"""
Restart extraction script with resume functionality.
This script will check progress and resume from the last successfully completed article.
"""

import asyncio
import sys
import logging
import os
import shutil
from datetime import datetime

import dspy
from src.config import Config
from src.sheets_client import SheetsClient
from src.article_fetcher import ArticleFetcher
from src.data_extractor import DataExtractor
from src.progress_tracker import ProgressTracker


def backup_and_reset_database():
    """Backup existing progress database and start fresh."""
    progress_db = "progress.db"
    
    if os.path.exists(progress_db):
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"old_progress_{timestamp}.db"
        
        shutil.move(progress_db, backup_name)
        logger.info(f"📦 Backed up existing progress database to: {backup_name}")
    else:
        logger.info("📋 No existing progress database found - starting fresh")


def configure_dspy():
    """Configure DSPy with Azure OpenAI."""
    try:
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
        
        logger.info("🤖 DSPy configured successfully with Azure OpenAI")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to configure DSPy: {e}")
        return False


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('extraction_restart.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def restart_extraction():
    """Main extraction function with database backup and fresh start."""
    logger.info("🚀 Starting systematic review data extraction with fresh database...")
    
    # Backup existing database and start fresh
    backup_and_reset_database()
    
    # Configure DSPy
    if not configure_dspy():
        logger.error("❌ Failed to configure DSPy - cannot proceed")
        return False
    
    try:
        # Initialize configuration
        config = Config()
        
        # Initialize components
        sheets_client = SheetsClient(config.sheets_config)
        article_fetcher = ArticleFetcher(config.extraction_config)
        data_extractor = DataExtractor(config.extraction_config)
        progress_tracker = ProgressTracker(config.tracking_config)
        
        logger.info("All components initialized")
        
        # Test connections
        if not await sheets_client.test_connection():
            logger.error("Google Sheets connection failed")
            return False
        
        logger.info("✅ Google Sheets connection verified")
        
        # Check progress and find resume point
        summary = progress_tracker.get_progress_summary()
        logger.info(f"Progress summary: {summary}")
        
        # Get all articles
        articles = await sheets_client.get_articles()
        logger.info(f"Found {len(articles)} total articles")
        
        # Determine articles to process (resume logic)
        processed_articles = progress_tracker.get_processed_articles()
        articles_to_process = []
        
        for article in articles:
            article_id = article.get('id') or f"row_{article.get('row_number')}"
            if article_id not in processed_articles:
                articles_to_process.append(article)
        
        if not articles_to_process:
            logger.info("🎉 All articles have been processed!")
            # Show final summary
            final_summary = progress_tracker.get_progress_summary()
            logger.info(f"Final summary: {final_summary}")
            return True
        
        logger.info(f"📋 Found {len(articles_to_process)} articles to process (resuming from last position)")
        
        # Process remaining articles
        success_count = 0
        error_count = 0
        
        for i, article in enumerate(articles_to_process, 1):
            article_id = article.get('id') or f"row_{article.get('row_number')}"
            title_short = article.get('title', 'Unknown')[:50]
            
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing article {i}/{len(articles_to_process)}: {title_short}")
            logger.info(f"Article ID: {article_id}")
            logger.info(f"{'='*80}")
            
            try:
                # Start tracking
                progress_tracker.start_processing(article_id, article)
                
                # Fetch article content
                logger.info("🔍 Fetching article content...")
                result = await article_fetcher.fetch_article(article)
                
                if result is None:
                    logger.warning("❌ No text content found for article")
                    progress_tracker.log_failure(article_id, "No text content found", "fetch")
                    error_count += 1
                    continue
                
                # Handle different return types from fetch_article
                if isinstance(result, tuple):
                    text, metadata = result
                else:
                    # Single return value (either text or metadata)
                    text = result if isinstance(result, str) and len(result) > 500 else ""
                    metadata = article  # Use original article metadata
                
                if not text:
                    logger.warning("❌ No text content found for article")
                    progress_tracker.log_failure(article_id, "No text content found", "fetch")
                    error_count += 1
                    continue
                
                logger.info(f"✅ Fetched {len(text)} characters of content")
                
                # Extract data with aligned signatures
                logger.info("🤖 Extracting data...")
                extracted_data = await data_extractor.extract_all_data(text, metadata)
                
                if not extracted_data:
                    logger.warning("❌ No data extracted")
                    progress_tracker.log_failure(article_id, "No data extracted", "extract")
                    error_count += 1
                    continue
                
                logger.info(f"✅ Extracted {len(extracted_data)} data categories")
                
                # Update sheets with extracted data
                logger.info("📊 Updating Google Sheets...")
                sheets_updated = 0
                
                for category, data in extracted_data.items():
                    if not data:
                        continue
                    
                    try:
                        # Map category to sheet name
                        sheet_mapping = {
                            'study_characteristics': 'Study Characteristics',
                            'population_characteristics': 'Population Characteristics', 
                            'interventions': 'Interventions & Comparators',
                            'primary_outcomes': 'Primary Outcomes (SSI Epidemiology & AMR)',
                            'secondary_outcomes': 'Secondary Outcomes (Clinical & Economic Impact)',
                            'drivers_innovations': 'Drivers, Innovations & Policy Context'
                        }
                        
                        sheet_name = sheet_mapping.get(category)
                        if sheet_name:
                            # Convert keys to exact column names
                            if category == 'study_characteristics':
                                sheet_data = {
                                    'Author': data.get('author', ''),
                                    'Year of publication': data.get('year_of_publication', ''),
                                    'Title of paper': data.get('title_of_paper', ''),
                                    'Country/Countries': data.get('country_countries', ''),
                                    'Study Design': data.get('study_design', ''),
                                    'Study Period': data.get('study_period', ''),
                                    'Setting': data.get('setting', '')
                                }
                            elif category == 'population_characteristics':
                                sheet_data = {
                                    'Total Sample Size (N)': data.get('total_sample_size_n', ''),
                                    'Population  Description': data.get('population_description', ''),
                                    'Inclusion Criteria': data.get('inclusion_criteria', ''),
                                    'Exclusion Criteria': data.get('exclusion_criteria', ''),
                                    'Age (Mean/Median & SD/IQR)': data.get('age_mean_median_sd_iqr', ''),
                                    'Sex (%Female)': data.get('sex_percent_female', ''),
                                    'Surgical Speciality ': data.get('surgical_speciality', ''),
                                    'Specific Procedures': data.get('specific_procedures', '')
                                }
                            elif category == 'interventions':
                                sheet_data = {
                                    'Intervention Group (N)': data.get('intervention_group_n', ''),
                                    'Intervention Details': data.get('intervention_details', ''),
                                    'Comparator Group (N)': data.get('comparator_group_n', ''),
                                    'Comparator Details': data.get('comparator_details', ''),
                                    'Adherence to Guidelines (%)': data.get('adherence_to_guidelines_percent', '')
                                }
                            elif category == 'primary_outcomes':
                                sheet_data = {
                                    'Total Procedures (N)': data.get('total_procedures_n', ''),
                                    'Total SSIs (N)': data.get('total_ssis_n', ''),
                                    'SSI Incidence Rate (%)': data.get('ssi_incidence_rate_percent', ''),
                                    'Method of SSI Diagnosis': data.get('method_of_ssi_diagnosis', ''),
                                    'Total SSI Isolates (N)': data.get('total_ssi_isolates_n', ''),
                                    'Pathogen 1 Name': data.get('pathogen_1_name', ''),
                                    'Pathogen 1 Resistance Profile': data.get('pathogen_1_resistance_profile', ''),
                                    'Pathogen 2 Name': data.get('pathogen_2_name', ''),
                                    'Pathogen 2 Resistance Profile': data.get('pathogen_2_resistance_profile', ''),
                                    'Resistance to WHO Critical Antibiotics': data.get('resistance_to_who_critical_antibiotics', '')
                                }
                            elif category == 'secondary_outcomes':
                                sheet_data = {
                                    'Morbidity - Additional Hospital Stay (Days)': data.get('morbidity_additional_hospital_stay_days', ''),
                                    'Morbidity - Re-operation Rate (%)': data.get('morbidity_re_operation_rate_percent', ''),
                                    'Morbidity - Readmission Rate (%)': data.get('morbidity_readmission_rate_percent', ''),
                                    'Mortality - SSI Attributable Rate (%)': data.get('mortality_ssi_attributable_rate_percent', ''),
                                    'Mortality - 30-day Post-op (%)': data.get('mortality_30_day_post_op_percent', ''),
                                    'Mortality - 90-day Post-op (%)': data.get('mortality_90_day_post_op_percent', ''),
                                    'Hospital Burden - Total Length of Stay (Days)': data.get('hospital_burden_total_length_of_stay_days', ''),
                                    'Economic - Direct Costs (USD/Local Currency)': data.get('economic_direct_costs_usd_local_currency', ''),
                                    'Economic - Indirect Costs (USD/Local Currency)': data.get('economic_indirect_costs_usd_local_currency', '')
                                }
                            elif category == 'drivers_innovations':
                                sheet_data = {
                                    'Reported Drivers of AMR': data.get('reported_drivers_of_amr', ''),
                                    'Interventions/Innovations Described': data.get('interventions_innovations_described', ''),
                                    'Gaps Identified by Authors': data.get('gaps_identified_by_authors', ''),
                                    'Policy Response/Capacity': data.get('policy_response_capacity', '')
                                }
                            else:
                                continue
                            
                            # Use the correct SheetsClient method
                            await sheets_client.update_extracted_data(str(article_id), {category: data})
                            sheets_updated += 1
                            logger.info(f"✅ Updated sheet: {sheet_name}")
                            
                    except Exception as sheet_error:
                        logger.error(f"❌ Error updating sheet {sheet_name}: {sheet_error}")
                
                if sheets_updated > 0:
                    # Log successful extraction
                    progress_tracker.log_success(article_id, extracted_data)
                    success_count += 1
                    logger.info(f"🎉 Successfully processed article {i}/{len(articles_to_process)}")
                else:
                    progress_tracker.log_failure(article_id, "No sheets updated", "update")
                    error_count += 1
                
            except Exception as e:
                logger.error(f"❌ Error processing article {article_id}: {str(e)}")
                progress_tracker.log_failure(article_id, str(e), "processing")
                error_count += 1
        
        # Final summary
        logger.info(f"\n{'='*80}")
        logger.info("EXTRACTION COMPLETED")
        logger.info(f"{'='*80}")
        logger.info(f"✅ Successfully processed: {success_count}")
        logger.info(f"❌ Errors: {error_count}")
        logger.info(f"📊 Total processed in this session: {success_count + error_count}")
        
        final_summary = progress_tracker.get_progress_summary()
        logger.info(f"📈 Overall progress: {final_summary}")
        
        return True
        
    except KeyboardInterrupt:
        logger.info("\n⏸️  Extraction paused by user")
        logger.info("📌 Progress has been saved. Run this script again to resume.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Critical error during extraction: {str(e)}")
        return False


def main():
    """Main entry point."""
    print("🚀 Starting systematic review data extraction with resume functionality...")
    print("💡 You can press Ctrl+C to pause and resume later")
    
    success = asyncio.run(restart_extraction())
    
    if success:
        print("\n🎉 Extraction completed successfully!")
    else:
        print("\n❌ Extraction failed. Check logs for details.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
