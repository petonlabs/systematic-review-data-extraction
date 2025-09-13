"""
Data extraction module using DSPy for systematic review.
Aligned with exact Google Sheets columns for consistent data extraction.
"""

import logging
from typing import Dict, Any

import dspy

from src.config import ExtractionConfig


class StudyCharacteristicsSignature(dspy.Signature):
    """Extract study characteristics matching exact sheet columns."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    author = dspy.OutputField(desc="First author surname only (e.g., 'Smith', 'Patel')")
    year_of_publication = dspy.OutputField(desc="Publication year as 4-digit number (e.g., '2023', '2022')")
    title_of_paper = dspy.OutputField(desc="Full paper title, concise (e.g., 'Surgical site infections in cardiac surgery')")
    country_countries = dspy.OutputField(desc="Study country/countries (e.g., 'USA', 'Kenya, Uganda', 'Multi-country')")
    study_design = dspy.OutputField(desc="Study design briefly (e.g., 'RCT', 'Cohort study', 'Cross-sectional')")
    study_period = dspy.OutputField(desc="Study time period (e.g., '2020-2022', 'Jan-Dec 2021', '6 months')")
    setting = dspy.OutputField(desc="Study setting briefly (e.g., 'Tertiary hospital', 'ICU', 'Community clinics')")


class PopulationCharacteristicsSignature(dspy.Signature):
    """Extract population characteristics matching exact sheet columns."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    total_sample_size = dspy.OutputField(desc="Total study participants as number (e.g., '456', '1,234')")
    population_description = dspy.OutputField(desc="Population described briefly (e.g., 'Adult surgical patients', 'Children under 5')")
    inclusion_criteria = dspy.OutputField(desc="Main inclusion criteria, concise (e.g., 'Adults >18, elective surgery')")
    exclusion_criteria = dspy.OutputField(desc="Main exclusion criteria, concise (e.g., 'Immunocompromised, emergency cases')")
    age_mean_median = dspy.OutputField(desc="Age statistics (e.g., 'Mean 45.2±12.3', 'Median 38 (IQR 25-52)')")
    sex_distribution = dspy.OutputField(desc="Gender breakdown (e.g., '60% female', 'M:F = 1.2:1', '45% male')")
    comorbidities = dspy.OutputField(desc="Main comorbidities mentioned (e.g., 'Diabetes 35%, HTN 42%')")
    surgery_type = dspy.OutputField(desc="Type of surgery (e.g., 'Cardiac', 'Orthopedic', 'Mixed surgical procedures')")


class InterventionsSignature(dspy.Signature):
    """Extract interventions & comparators matching exact sheet columns."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    intervention_group_n = dspy.OutputField(desc="Intervention group size as number (e.g., '245', '1,120')")
    intervention_details = dspy.OutputField(desc="Intervention described briefly (e.g., 'Prophylactic cefazolin', 'Bundle approach')")
    comparator_group_n = dspy.OutputField(desc="Control group size as number (e.g., '250', '1,080')")
    comparator_details = dspy.OutputField(desc="Comparator described briefly (e.g., 'Standard care', 'Placebo', 'Historical control')")
    adherence_to_guidelines = dspy.OutputField(desc="Guideline adherence percentage (e.g., '85%', '92% compliance', 'High adherence')")


class PrimaryOutcomesSignature(dspy.Signature):
    """Extract primary outcomes matching exact sheet columns."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    total_procedures = dspy.OutputField(desc="Total number of procedures as number (e.g., '450', '1,234', '89')")
    total_ssis = dspy.OutputField(desc="Total SSI cases as number (e.g., '45', '78', '12')")
    ssi_incidence_rate = dspy.OutputField(desc="SSI rate as percentage (e.g., '10.2%', '15.7%', '6.8%')")
    method_of_ssi_diagnosis = dspy.OutputField(desc="Diagnostic method briefly (e.g., 'CDC criteria', 'Clinical assessment', 'WHO guidelines')")
    total_ssi_isolates = dspy.OutputField(desc="Total isolates cultured as number (e.g., '67', '134', 'Not reported')")
    pathogen_1_name_name_of_the_most_common_isolated_pathogen = dspy.OutputField(desc="Most common pathogen name (e.g., 'S. aureus', 'E. coli', 'K. pneumoniae')")
    pathogen_1_resistance_list_antibiotic_resistance = dspy.OutputField(desc="Resistance pattern for pathogen 1 (e.g., 'MRSA 45%', 'ESBL positive', 'MDR')")
    pathogen_2_name_name_of_the_2nd_most_common_pathogen = dspy.OutputField(desc="Second most common pathogen name (e.g., 'P. aeruginosa', 'A. baumannii')")
    pathogen_2_resistance_list_antibiotic_resistance_percent = dspy.OutputField(desc="Resistance pattern for pathogen 2 (e.g., 'Carbapenem resistant', 'MDR 67%')")
    resistance_to_who_critical_abx_any_specific_data_on_resistance_to_who_critical_important_antibiotics = dspy.OutputField(desc="WHO critical antibiotic resistance data (e.g., 'Carbapenem 23%', 'Colistin 12%', 'Not assessed')")


class SecondaryOutcomesSignature(dspy.Signature):
    """Extract secondary outcomes matching exact sheet columns."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    morbidity_additional_hospital_stay_days = dspy.OutputField(desc="Extra hospital days as number (e.g., '7.2 days', '14 days', '5.8 days')")
    morbidity_re_operation_rate = dspy.OutputField(desc="Re-operation rate as percentage (e.g., '12.5%', '23 cases', '8.9%')")
    morbidity_readmission_rate = dspy.OutputField(desc="Readmission rate as percentage (e.g., '8.3%', '15 out of 200', '6.7%)")
    mortality_ssi_attributable_rate = dspy.OutputField(desc="SSI-related death rate as percentage (e.g., '5.2%', '12 out of 100 patients', '3.8%')")
    mortality_30_day_post_op = dspy.OutputField(desc="30-day mortality rate (e.g., '2.1%', '5 patients', '1.8%')")
    mortality_90_day_post_op = dspy.OutputField(desc="90-day mortality rate (e.g., '4.5%', '8 patients', '3.2%')")
    hospital_burden_total_length_of_stay_days = dspy.OutputField(desc="Total length of stay as number (e.g., '12.4 days', '21 days', '15.7 days')")
    economic_direct_costs = dspy.OutputField(desc="Direct costs (e.g., '$5,420', '€3,200', '$8,750')")
    economic_indirect_costs = dspy.OutputField(desc="Indirect costs (e.g., '$2.4M', '€1.8M', '$5.6M')")


class DriversInnovationsSignature(dspy.Signature):
    """Extract drivers, innovations & policy context matching exact sheet columns."""
    article_text = dspy.InputField(desc="Full text or abstract of the research article")
    
    reported_drivers_of_amr = dspy.OutputField(desc="AMR drivers mentioned, comma-separated (e.g., 'Overuse of antibiotics, Poor infection control')")
    interventions_innovations_described = dspy.OutputField(desc="Innovations described briefly (e.g., 'Bundle approach, New diagnostic tool')")
    gaps_identified_by_authors = dspy.OutputField(desc="Gaps mentioned by authors, comma-separated")
    policy_response_capacity = dspy.OutputField(desc="Policy responses mentioned (e.g., 'Stewardship program needed', 'Surveillance enhancement')")


class DataExtractor:
    """Data extractor aligned with exact Google Sheets structure."""
    
    def __init__(self, config: ExtractionConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.study_extractor = dspy.ChainOfThought(StudyCharacteristicsSignature)
        self.population_extractor = dspy.ChainOfThought(PopulationCharacteristicsSignature)
        self.interventions_extractor = dspy.ChainOfThought(InterventionsSignature)
        self.primary_outcomes_extractor = dspy.ChainOfThought(PrimaryOutcomesSignature)
        self.secondary_outcomes_extractor = dspy.ChainOfThought(SecondaryOutcomesSignature)
        self.drivers_extractor = dspy.ChainOfThought(DriversInnovationsSignature)
        
        self.logger.info("Data extraction modules initialized with exact sheet alignment")
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for optimal extraction."""
        if not text:
            return ""
        
        max_length = 10000
        if len(text) > max_length:
            text = text[:max_length] + "..."
            self.logger.info(f"Text truncated to {len(text)} characters")
        
        return text.strip()
    
    async def extract_all_data(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract all data categories with exact Google Sheets field mapping."""
        try:
            article_title = metadata.get('title', 'Unknown article') if metadata else 'Unknown article'
            self.logger.info(f"Starting data extraction for article: {article_title[:50]}...")
            
            processed_text = self._preprocess_text(text)
            if not processed_text:
                self.logger.warning("No text to process after preprocessing")
                return {}
            
            extracted_data = {}
            
            # Extract study characteristics
            study_result = self.study_extractor(article_text=processed_text)
            extracted_data['study_characteristics'] = {
                'Author': study_result.author,
                'Year of publication': study_result.year_of_publication,
                'Title of paper': study_result.title_of_paper,
                'Country/Countries': study_result.country_countries,
                'Study Design': study_result.study_design,
                'Study Period': study_result.study_period,
                'Setting': study_result.setting
            }
            self.logger.info("Study characteristics extracted successfully")
            
            # Extract population characteristics
            population_result = self.population_extractor(article_text=processed_text)
            extracted_data['population_characteristics'] = {
                'Total Sample Size (N)': population_result.total_sample_size,
                'Population  Description': population_result.population_description,
                'Inclusion Criteria': population_result.inclusion_criteria,
                'Exclusion Criteria': population_result.exclusion_criteria,
                'Age (Mean/Median & SD/IQR)': population_result.age_mean_median,
                'Sex Distribution': population_result.sex_distribution,
                'Comorbidities': population_result.comorbidities,
                'Surgery Type': population_result.surgery_type
            }
            self.logger.info("Population characteristics extracted successfully")
            
            # Extract interventions
            interventions_result = self.interventions_extractor(article_text=processed_text)
            extracted_data['interventions'] = {
                'Intervention Group (N)': interventions_result.intervention_group_n,
                'Intervention Details': interventions_result.intervention_details,
                'Comparator Group (N)': interventions_result.comparator_group_n,
                'Comparator Details': interventions_result.comparator_details,
                'Adherence to Guidelines (%)': interventions_result.adherence_to_guidelines
            }
            self.logger.info("Interventions extracted successfully")
            
            # Extract primary outcomes with exact field mapping
            primary_result = self.primary_outcomes_extractor(article_text=processed_text)
            extracted_data['primary_outcomes'] = {
                'Total Procedures': primary_result.total_procedures,
                'Total SSIs': primary_result.total_ssis,
                'SSI Incidence Rate': primary_result.ssi_incidence_rate,
                'Method of SSI Diagnosis': primary_result.method_of_ssi_diagnosis,
                'Total SSI Isolates': primary_result.total_ssi_isolates,
                'Pathogen 1 Name (Name of the most common isolated pathogen)': primary_result.pathogen_1_name_name_of_the_most_common_isolated_pathogen,
                'Pathogen 1 Resistance (List antibiotic resistance)': primary_result.pathogen_1_resistance_list_antibiotic_resistance,
                'Pathogen 2 Name (Name of the 2nd most common pathogen)': primary_result.pathogen_2_name_name_of_the_2nd_most_common_pathogen,
                'Pathogen 2 Resistance (List antibiotic resistance %)': primary_result.pathogen_2_resistance_list_antibiotic_resistance_percent,
                'Resistance to WHO Critical Abx (Any specific data on resistance to WHO critical important antibiotics)': primary_result.resistance_to_who_critical_abx_any_specific_data_on_resistance_to_who_critical_important_antibiotics
            }
            self.logger.info("Primary outcomes extracted successfully")
            
            # Extract secondary outcomes with exact field mapping
            secondary_result = self.secondary_outcomes_extractor(article_text=processed_text)
            extracted_data['secondary_outcomes'] = {
                'Morbidity - Additional Hospital Stay (days)': secondary_result.morbidity_additional_hospital_stay_days,
                'Morbidity - Re-opertation rate (%)': secondary_result.morbidity_re_operation_rate,
                'Morbidity - Readmission rate (%)': secondary_result.morbidity_readmission_rate,
                'Mortality - SSI attributable rate (%)': secondary_result.mortality_ssi_attributable_rate,
                'Mortality - 30-day post-op': secondary_result.mortality_30_day_post_op,
                'Mortality - 90-day post-op (%)': secondary_result.mortality_90_day_post_op,
                'Hospital burden - Total length of stay (days)': secondary_result.hospital_burden_total_length_of_stay_days,
                'Economic - direct costs': secondary_result.economic_direct_costs,
                'Economic - indirect costs': secondary_result.economic_indirect_costs
            }
            self.logger.info("Secondary outcomes extracted successfully")
            
            # Extract drivers and innovations
            drivers_result = self.drivers_extractor(article_text=processed_text)
            extracted_data['drivers_innovations'] = {
                'Reported Drivers of AMR': drivers_result.reported_drivers_of_amr,
                'Interventions/Innovations Described': drivers_result.interventions_innovations_described,
                'Gaps Identified by Authors': drivers_result.gaps_identified_by_authors,
                'Policy Response/Capacity': drivers_result.policy_response_capacity
            }
            self.logger.info("Drivers and innovations extracted successfully")
            
            self.logger.info(f"Successfully extracted {len(extracted_data)} data categories")
            return extracted_data
            
        except Exception as e:
            self.logger.error(f"Error during data extraction: {str(e)}")
            raise
