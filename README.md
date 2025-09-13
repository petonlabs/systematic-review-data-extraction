# Systematic Review Data Extraction Tool

An automated tool for extracting structured data from research articles in systematic reviews using DSPy and large language models.

## 🎯 Purpose

This tool automates the time-intensive process of data extraction in systematic reviews by:

1. **Fetching articles** from Google Sheets containing DOIs/PMIDs
2. **Retrieving full-text content** from various sources (DOI resolution, Unpaywall, CrossRef, PubMed Central)
3. **Extracting structured data** using DSPy LLM agents for:
   - Study characteristics
   - Population characteristics
   - Interventions and comparators
   - Primary outcomes (SSI epidemiology and AMR)
   - Secondary outcomes (clinical and economic impact)
   - Drivers, innovations, and policy context
4. **Populating Google Sheets** with extracted data
5. **Tracking progress** and logging results

## 🏗️ Architecture

```
main.py → Orchestrates the entire process
├── src/config.py → Configuration management
├── src/sheets_client.py → Google Sheets API integration
├── src/article_fetcher.py → Article retrieval from multiple sources
├── src/data_extractor.py → DSPy-based data extraction
├── src/progress_tracker.py → Progress tracking with SQLite
└── src/rate_limiter.py → API rate limiting
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.13+
- uv package manager
- Azure OpenAI API access
- Google Cloud Project with Sheets API enabled

### 2. Installation

```bash
# Clone and setup
git clone <repository>
cd systematic-review-data-extraction

# Install dependencies
uv sync
```

### 3. Configuration

#### Azure OpenAI Setup
Create/verify your `.env` file:
```bash
# Azure OpenAI settings
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com
AZURE_OPENAI_API_VERSION=2025-04-01-preview
AZURE_OPENAI_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name

# Optional: Email for API requests
CROSSREF_EMAIL=your-email@university.edu
UNPAYWALL_EMAIL=your-email@university.edu
```

#### Google Sheets Setup

1. **Enable Google Sheets API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create or select a project
   - Enable Google Sheets API and Google Drive API
   - Create credentials (OAuth 2.0 Client ID for desktop application)
   - Download as `credentials.json` in project root

2. **Verify Sheet Structure**:
   Your Google Sheet should have these tabs:
   - `articles` (with DOI/PMID columns)
   - `Study characteristics`
   - `Population characteristics`
   - `Interventions and comparators`
   - `Primary outcomes, (SSI epidemiology and AMR)`
   - `Secondary outcomes (clinical and economic impact)`
   - `Drivers, Innovations and policy context`

### 4. Test Setup

```bash
# Test the configuration
uv run python test_setup.py
```

This will verify:
- ✅ DSPy configuration with Azure OpenAI
- ✅ Progress tracking database
- ✅ Google Sheets connection (if credentials are set up)

### 5. Run Full Extraction

```bash
# Start the main extraction process
uv run python main.py
```

## 📊 Google Sheets Structure

### Required Sheets

1. **articles** - Input sheet with article metadata:
   - DOI column
   - PMID column (optional)
   - Title column (optional)
   - Other metadata columns

2. **Study characteristics** - Will be populated with:
   - Study type, design, setting
   - Country, duration, sample size

3. **Population characteristics** - Will be populated with:
   - Age range, gender distribution
   - Clinical conditions, inclusion/exclusion criteria

4. **Interventions and comparators** - Will be populated with:
   - Intervention details, comparators
   - Dosage and duration information

5. **Primary outcomes** - Will be populated with:
   - SSI incidence data
   - AMR patterns and resistance genes
   - Pathogen identification

6. **Secondary outcomes** - Will be populated with:
   - Length of stay, mortality, readmissions
   - Economic costs and quality of life measures

7. **Drivers, Innovations and policy context** - Will be populated with:
   - Risk factors, innovations
   - Policy implications and guidelines

## 🔧 Configuration Options

### Rate Limiting
```python
# In src/config.py
rate_limit_config = RateLimitConfig(
    sheets_requests_per_minute=60,
    api_requests_per_minute=30,
    azure_requests_per_minute=60
)
```

### Extraction Settings
```python
# In src/config.py
extraction_config = ExtractionConfig(
    max_tokens=4000,
    temperature=0.1,
    chunk_size=8000,  # For long articles
    overlap=500
)
```

## 📈 Progress Tracking

The tool maintains progress in several ways:

1. **SQLite Database** (`progress.db`):
   - Article processing status
   - Extracted data storage
   - Error logging

2. **Log Files** (`logs/`):
   - Timestamped execution logs
   - Detailed error messages
   - Processing statistics

3. **Export Options**:
   ```python
   # Export results
   tracker.export_results("results.csv", format="csv")
   tracker.export_results("results.json", format="json")
   ```

## 🛠️ Article Fetching Strategy

The tool attempts to retrieve full-text articles from multiple sources:

1. **Direct DOI Resolution** - Try to access article directly
2. **Unpaywall API** - Find open access versions
3. **CrossRef API** - Get metadata and links
4. **PubMed Central** - For PMC articles
5. **arXiv** - For preprints
6. **Metadata Only** - If full text unavailable

## 🧠 DSPy Data Extraction

Uses specialized DSPy signatures for each data category:

```python
class StudyCharacteristicsSignature(dspy.Signature):
    """Extract study characteristics from research article."""
    article_text = dspy.InputField(desc="Full text or abstract")
    study_type = dspy.OutputField(desc="Type of study (RCT, cohort, etc.)")
    # ... more fields
```

## 📊 Monitoring and Debugging

### Check Progress
```python
# Get progress summary
python -c "
from src.progress_tracker import ProgressTracker
from src.config import Config
tracker = ProgressTracker(Config().tracking_config)
print(tracker.get_progress_summary())
"
```

### View Failed Articles
```python
# Get failed articles for retry
failed = tracker.get_failed_articles()
for article in failed:
    print(f"{article['id']}: {article['error_message']}")
```

### Monitor Rate Limits
```python
# Check rate limit status
from src.rate_limiter import RateLimiter
limiter = RateLimiter(Config().rate_limit_config)
print(limiter.get_status())
```

## ⚠️ Important Notes

1. **Context Window Management**: The tool automatically chunks long articles to fit within LLM context windows

2. **Rate Limiting**: Respects API rate limits for Google Sheets, article sources, and Azure OpenAI

3. **Error Handling**: Continues processing if individual articles fail, logging errors for review

4. **Resume Capability**: Can resume processing from where it left off using the progress database

5. **Data Quality**: Uses Chain-of-Thought reasoning in DSPy for better extraction quality

## 🆘 Troubleshooting

### Common Issues

1. **Google Sheets Authentication**:
   ```bash
   # Delete token.json and re-authenticate
   rm token.json
   python test_setup.py
   ```

2. **Azure OpenAI Connection**:
   ```bash
   # Verify credentials
   echo $AZURE_OPENAI_KEY
   echo $AZURE_OPENAI_ENDPOINT
   ```

3. **Article Retrieval Failures**:
   - Check DOI formatting
   - Verify network connectivity
   - Review rate limiting settings

4. **Database Issues**:
   ```bash
   # Reset progress database
   rm progress.db
   python test_setup.py
   ```

### Debug Mode
```bash
# Run with debug logging
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import asyncio
from main import main
asyncio.run(main())
"
```

## 📝 License

This project is designed for academic research purposes. Please ensure compliance with API terms of service and institutional policies.

## 🤝 Contributing

1. Follow SOLID principles
2. Add contextual logging
3. Include tests for new features
4. Update documentation

## 📞 Support

For issues:
1. Check the troubleshooting section
2. Review log files in `logs/`
3. Check the progress database for error details
4. Ensure all API credentials are valid
