#!/usr/bin/env python3
"""Debug script to check column alignment issues."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.sheets_client import SheetsClient

async def main():
    config = Config()
    client = SheetsClient(config.sheets_config)
    
    if not await client.authenticate():
        print("❌ Failed to authenticate")
        return
    
    # Check Primary Outcomes sheet
    print("=== Primary Outcomes (SSI Epidemiology & AMR) ===")
    headers = await client.get_sheet_headers('Primary Outcomes (SSI Epidemiology & AMR)')
    expected_fields = [
        'total_procedures',
        'total_ssis', 
        'ssi_incidence_rate',
        'method_of_ssi_diagnosis',
        'total_ssi_isolates',
        'pathogen_1_name_name_of_the_most_common_isolated_pathogen',
        'pathogen_1_resistance_list_antibiotic_resistance',
        'pathogen_2_name_name_of_the_2nd_most_common_pathogen',
        'pathogen_2_resistance_list_antibiotic_resistance_percent',
        'resistance_to_who_critical_abx_any_specific_data_on_resistance_to_who_critical_important_antibiotics'
    ]
    
    print(f"Actual headers ({len(headers)}):")
    for i, header in enumerate(headers, 1):
        print(f"  {i:2d}. '{header}'")
    
    print(f"\nExpected fields ({len(expected_fields)}):")
    for i, field in enumerate(expected_fields, 1):
        print(f"  {i:2d}. {field}")
    
    # Check Secondary Outcomes sheet
    print("\n=== Secondary Outcomes (Clinical & Economic Impact) ===")
    headers2 = await client.get_sheet_headers('Secondary Outcomes (Clinical & Economic Impact)')
    expected_fields2 = [
        'mortality',
        'morbidity_additional_hospital_stay_days',
        'morbidity_icu_stay_days', 
        'morbidity_total_los_days',
        'morbidity_readmission_rate',
        're_operation_revision_surgery',
        'economic_additional_cost_attributable_to_ssi_per_patient',
        'economic_total_additional_cost_healthcare_system',
        'patient_reported_outcomes_pain_function_qol'
    ]
    
    print(f"Actual headers ({len(headers2)}):")
    for i, header in enumerate(headers2, 1):
        print(f"  {i:2d}. '{header}'")
    
    print(f"\nExpected fields ({len(expected_fields2)}):")
    for i, field in enumerate(expected_fields2, 1):
        print(f"  {i:2d}. {field}")

if __name__ == "__main__":
    asyncio.run(main())
