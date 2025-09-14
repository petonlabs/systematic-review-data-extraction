# Systematic Review Data Extraction Tool

An automated tool for extracting structured data from research articles in systematic reviews using DSPy and large language models. **Now supports both web-based and PDF-based extraction methods with Cloudflare R2 storage!**

## 🎯 Purpose

This tool automates the time-intensive process of data extraction in systematic reviews by:

1. **Fetching articles** from Google Sheets containing DOIs/PMIDs
2. **Retrieving full-text content** using two methods:
   - **Web-based extraction**: Direct fetching from various sources (DOI resolution, Unpaywall, CrossRef, PubMed Central)
   - **PDF-based extraction**: Download, store, and process PDFs with memory-efficient text extraction
3. **Extracting structured data** using DSPy LLM agents for:
   - Study characteristics
   - Population characteristics
   - Interventions and comparators
   - Primary outcomes (SSI epidemiology and AMR)
   - Secondary outcomes (clinical and economic impact)
   - Drivers, innovations, and policy context
4. **Populating Google Sheets** with extracted data
5. **Tracking progress** and logging results with method persistence

## 🚀 New Features

### PDF-Based Extraction
- **PDF Download & Storage**: Automatically downloads PDFs and stores them in Cloudflare R2 for systematic archiving
- **Memory-Efficient Processing**: Processes large PDFs in chunks to manage memory usage
- **Fallback Mechanism**: Falls back to web-based extraction if PDF processing fails
- **Progress Persistence**: Remembers your chosen extraction method and can resume from where you left off

### Enhanced Configuration
- **Method Selection**: Choose between web-based or PDF-based extraction at runtime
- **Cloudflare R2 Integration**: Secure, scalable storage for research article PDFs
- **Flexible Configuration**: Support for both extraction methods in the same tool

## 🏗️ Architecture

```
enhanced_main.py → New enhanced orchestrator with method selection
├── src/config.py → Enhanced configuration (PDF + R2 settings)
├── src/sheets_client.py → Google Sheets API integration
├── src/enhanced_article_fetcher.py → NEW: PDF-first article retrieval
├── src/pdf_processor.py → NEW: Memory-efficient PDF text extraction
├── src/cloudflare_r2.py → NEW: PDF storage in Cloudflare R2
├── src/extraction_mode_manager.py → NEW: Method selection & state management
├── src/data_extractor.py → DSPy-based data extraction
├── src/progress_tracker.py → Enhanced progress tracking
└── src/rate_limiter.py → API rate limiting
```

### Extraction Methods

**Web-based Extraction (Original)**
- Fetches articles directly from web sources
- Uses DOI resolution, Unpaywall, CrossRef, PMC
- Faster for immediately accessible content
- No additional storage requirements

**PDF-based Extraction (New)**
- Downloads PDFs from multiple sources
- Stores PDFs in Cloudflare R2 for archival
- Extracts text using memory-efficient processing
- Better for systematic collection and offline processing
- Supports large-scale archival workflows

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
Copy the template and configure your `.env` file:
```bash
cp .env.template .env
# Edit .env with your credentials
```

Required settings for `.env`:
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

# For PDF-based extraction: Cloudflare R2 settings
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your-r2-access-key-id
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key
R2_BUCKET_NAME=systematic-review-pdfs
```

#### Cloudflare R2 Setup (for PDF-based extraction)
1. **Create Cloudflare R2 Account**: 
   - Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
   - Navigate to R2 Object Storage
   - Create a new bucket (e.g., `systematic-review-pdfs`)

2. **Get R2 API Credentials**:
   - Go to "Manage R2 API tokens"
   - Create a new API token with R2 permissions
   - Note down the Account ID, Access Key ID, and Secret Access Key

3. **Configure R2 Settings**:
   - Update your `.env` file with the R2 credentials
   - The endpoint URL format: `https://<account-id>.r2.cloudflarestorage.com`

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
# Test the enhanced functionality
PYTHONPATH=. python3 tests/test_enhanced_functionality.py

# Test both extraction methods with a single article
PYTHONPATH=. python3 tests/test_enhanced_single_article.py
```

This will verify:
- ✅ DSPy configuration with Azure OpenAI
- ✅ PDF processing capabilities
- ✅ Cloudflare R2 connection (if configured)
- ✅ Enhanced article fetcher
- ✅ Extraction mode management
- ✅ Google Sheets connection (if credentials are set up)

### 5. Run Enhanced Extraction

```bash
# Start the enhanced extraction process with method selection
python3 enhanced_main.py
```

**Interactive Method Selection:**
- Choose between web-based and PDF-based extraction
- Configure PDF storage options
- Resume from previous runs automatically

**Alternatively, use the original script:**
```bash
# Use the original main script (web-based only)
python3 main.py
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

### Web-Based Method (Original)
The tool attempts to retrieve full-text articles from multiple sources:

1. **Direct DOI Resolution** - Try to access article directly
2. **Unpaywall API** - Find open access versions
3. **CrossRef API** - Get metadata and links
4. **PubMed Central** - For PMC articles
5. **arXiv** - For preprints
6. **Metadata Only** - If full text unavailable

### PDF-Based Method (New)
Enhanced PDF-first approach with systematic archival:

1. **Check R2 Storage** - Look for previously stored PDFs
2. **Multi-source PDF Download** - Fetch PDFs from:
   - Direct DOI resolution
   - Unpaywall API
   - PubMed Central
   - arXiv
   - Publisher direct links
3. **Store in R2** - Archive PDFs in Cloudflare R2
4. **Memory-Efficient Extraction** - Process PDFs in chunks
5. **Fallback to Web** - Use web-based method if PDF fails

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
