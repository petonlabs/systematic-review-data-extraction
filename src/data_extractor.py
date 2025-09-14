"""
Data extraction module using DSPy for systematic review.
"""

import logging
from typing import Dict, Any

import dspy

from src.config import ExtractionConfig


# Field name mapping for Google Sheets columns
FIELD_NAME_MAPPING = {
    'study_characteristics': {
        'author': 'Author',
        'year_of_publication': 'Year of publication',
        'title_of_paper': 'Title of paper', 
        'country_countries': 'Country/Countries',
        'study_design': 'Study Design',
        'study_period': 'Study Period',
        'setting': 'Setting'
    },
    'population_characteristics': {
        'total_sample_size': 'Total Sample Size (N)',
        'population_description': 'Population  Description',
        'inclusion_criteria': 'Inclusion Criteria',
        'exclusion_criteria': 'Exclusion Criteria',
        'age_mean_median': 'Age (Mean/Median & SD/IQR)',
        'sex_distribution': 'Sex Distribution',
        'comorbidities': 'Comorbidities',
        'surgery_type': 'Surgery Type'
    },
    'interventions': {
        'intervention_group_n': 'Intervention Group (N)',
        'intervention_details': 'Intervention Details',
        'comparator_group_n': 'Comparator Group (N)',
        'comparator_details': 'Comparator Details',
        'adherence_to_guidelines': 'Adherence to Guidelines (%)'
    },
    'primary_outcomes': {
        'total_procedures': 'Total Procedures',
        'total_ssis': 'Total SSIs',
        'ssi_incidence_rate': 'SSI Incidence Rate',
        'method_of_ssi_diagnosis': 'Method of SSI Diagnosis',
        'total_ssi_isolates': 'Total SSI Isolates',
        'pathogen_1_name': 'Pathogen 1 Name (Name of the most common isolated pathogen)',
        'pathogen_1_resistance': 'Pathogen 1 Resistance (List antibiotic resistance)',
        'pathogen_2_name': 'Pathogen 2 Name (Name of the 2nd most common pathogen)',
        'pathogen_2_resistance': 'Pathogen 2 Resistance (List antibiotic resistance %)',
        'resistance_to_who_critical_abx': 'Resistance to WHO Critical Abx (Any specific data on resistance to WHO critical important antibiotics)'
    },
    'secondary_outcomes': {
        'morbidity_additional_hospital_stay': 'Morbidity - Additional Hospital Stay (days)',
        'morbidity_re_operation_rate': 'Morbidity - Re-opertation rate (%)',
        'morbidity_readmission_rate': 'Morbidity - Readmission rate (%)',
        'mortality_ssi_attributable_rate': 'Mortality - SSI attributable rate (%)',
        'mortality_30_day_post_op': 'Mortality - 30-day post-op',
        'mortality_90_day_post_op': 'Mortality - 90-day post-op (%)',
        'hospital_burden_total_length_of_stay': 'Hospital burden - Total length of stay (days)',
        'economic_direct_costs': 'Economic - direct costs',
        'economic_indirect_costs': 'Economic - indirect costs'
    },
    'drivers_innovations': {
        'reported_drivers_of_amr': 'Reported Drivers of AMR',
        'interventions_innovations_described': 'Interventions/Innovations Described',
        'gaps_identified_by_authors': 'Gaps Identified by Authors',
        'policy_response_capacity': 'Policy Response/Capacity'
    }
}


class StudyCharacteristicsSignature(dspy.Signature):
    """Extract study characteristics."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    author = dspy.OutputField(desc="First author surname only")
    year_of_publication = dspy.OutputField(desc="Publication year as 4-digit number")
    title_of_paper = dspy.OutputField(desc="Full paper title")
    country_countries = dspy.OutputField(desc="Study country/countries")
    study_design = dspy.OutputField(desc="Study design")
    study_period = dspy.OutputField(desc="Study time period")
    setting = dspy.OutputField(desc="Study setting")


class PopulationCharacteristicsSignature(dspy.Signature):
    """Extract population characteristics."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    total_sample_size = dspy.OutputField(desc="Total study participants as number")
    population_description = dspy.OutputField(desc="Population description")
    inclusion_criteria = dspy.OutputField(desc="Main inclusion criteria")
    exclusion_criteria = dspy.OutputField(desc="Main exclusion criteria")
    age_mean_median = dspy.OutputField(desc="Age statistics")
    sex_distribution = dspy.OutputField(desc="Gender breakdown")
    comorbidities = dspy.OutputField(desc="Main comorbidities mentioned")
    surgery_type = dspy.OutputField(desc="Type of surgery")


class InterventionsSignature(dspy.Signature):
    """Extract interventions & comparators."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    intervention_group_n = dspy.OutputField(desc="Intervention group size as number")
    intervention_details = dspy.OutputField(desc="Intervention description")
    comparator_group_n = dspy.OutputField(desc="Control group size as number")
    comparator_details = dspy.OutputField(desc="Comparator description")
    adherence_to_guidelines = dspy.OutputField(desc="Guideline adherence percentage")


class PrimaryOutcomesSignature(dspy.Signature):
    """Extract primary outcomes."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    total_procedures = dspy.OutputField(desc="Total number of procedures")
    total_ssis = dspy.OutputField(desc="Total SSI cases")
    ssi_incidence_rate = dspy.OutputField(desc="SSI rate as percentage")
    method_of_ssi_diagnosis = dspy.OutputField(desc="Diagnostic method")
    total_ssi_isolates = dspy.OutputField(desc="Total isolates cultured")
    pathogen_1_name = dspy.OutputField(desc="Most common pathogen name")
    pathogen_1_resistance = dspy.OutputField(desc="Resistance pattern for pathogen 1")
    pathogen_2_name = dspy.OutputField(desc="Second most common pathogen name")
    pathogen_2_resistance = dspy.OutputField(desc="Resistance pattern for pathogen 2")
    resistance_to_who_critical_abx = dspy.OutputField(desc="WHO critical antibiotic resistance data")


class SecondaryOutcomesSignature(dspy.Signature):
    """Extract secondary outcomes."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    morbidity_additional_hospital_stay = dspy.OutputField(desc="Extra hospital days")
    morbidity_re_operation_rate = dspy.OutputField(desc="Re-operation rate")
    morbidity_readmission_rate = dspy.OutputField(desc="Readmission rate")
    mortality_ssi_attributable_rate = dspy.OutputField(desc="SSI-related death rate")
    mortality_30_day_post_op = dspy.OutputField(desc="30-day mortality rate")
    mortality_90_day_post_op = dspy.OutputField(desc="90-day mortality rate")
    hospital_burden_total_length_of_stay = dspy.OutputField(desc="Total length of stay")
    economic_direct_costs = dspy.OutputField(desc="Direct costs")
    economic_indirect_costs = dspy.OutputField(desc="Indirect costs")


class DriversInnovationsSignature(dspy.Signature):
    """Extract drivers, innovations & policy context."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    reported_drivers_of_amr = dspy.OutputField(desc="AMR drivers mentioned")
    interventions_innovations_described = dspy.OutputField(desc="Innovations described")
    gaps_identified_by_authors = dspy.OutputField(desc="Gaps mentioned by authors")
    policy_response_capacity = dspy.OutputField(desc="Policy responses mentioned")


class DataExtractor:
    """Data extractor for systematic review."""
    
    def __init__(self, config: ExtractionConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.study_extractor = dspy.ChainOfThought(StudyCharacteristicsSignature)
        self.population_extractor = dspy.ChainOfThought(PopulationCharacteristicsSignature)
        self.interventions_extractor = dspy.ChainOfThought(InterventionsSignature)
        self.primary_outcomes_extractor = dspy.ChainOfThought(PrimaryOutcomesSignature)
        self.secondary_outcomes_extractor = dspy.ChainOfThought(SecondaryOutcomesSignature)
        self.drivers_extractor = dspy.ChainOfThought(DriversInnovationsSignature)
        
        self.logger.info("Data extraction modules initialized")

    def _convert_fields_to_columns(self, category: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert DSPy field names to Google Sheets column headers."""
        mapping = FIELD_NAME_MAPPING.get(category, {})
        converted_data = {}
        
        for field_name, value in extracted_data.items():
            column_name = mapping.get(field_name, field_name)
            converted_data[column_name] = value
            
        return converted_data

    async def extract_data(self, article_text: str) -> Dict[str, Dict[str, Any]]:
        """Extract structured data from article text."""
        try:
            self.logger.info("Starting data extraction")

            # Extract each category
            study_chars = self.study_extractor(article_text=article_text)
            population_chars = self.population_extractor(article_text=article_text) 
            interventions = self.interventions_extractor(article_text=article_text)
            primary_outcomes = self.primary_outcomes_extractor(article_text=article_text)
            secondary_outcomes = self.secondary_outcomes_extractor(article_text=article_text)
            drivers = self.drivers_extractor(article_text=article_text)

            # Convert to column format
            extracted_data = {
                'study_characteristics': self._convert_fields_to_columns(
                    'study_characteristics', 
                    {k: v for k, v in study_chars.__dict__.items() if not k.startswith('_')}
                ),
                'population_characteristics': self._convert_fields_to_columns(
                    'population_characteristics',
                    {k: v for k, v in population_chars.__dict__.items() if not k.startswith('_')}
                ),
                'interventions': self._convert_fields_to_columns(
                    'interventions',
                    {k: v for k, v in interventions.__dict__.items() if not k.startswith('_')}
                ),
                'primary_outcomes': self._convert_fields_to_columns(
                    'primary_outcomes',
                    {k: v for k, v in primary_outcomes.__dict__.items() if not k.startswith('_')}
                ),
                'secondary_outcomes': self._convert_fields_to_columns(
                    'secondary_outcomes',
                    {k: v for k, v in secondary_outcomes.__dict__.items() if not k.startswith('_')}
                ),
                'drivers_innovations': self._convert_fields_to_columns(
                    'drivers_innovations',
                    {k: v for k, v in drivers.__dict__.items() if not k.startswith('_')}
                )
            }

            self.logger.info(f"Successfully extracted data for {len(extracted_data)} categories")
            return extracted_data

        except Exception as e:
            self.logger.error(f"Data extraction failed: {e}")
            raise
