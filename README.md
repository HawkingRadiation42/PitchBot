# PitchBot

AI-powered pitch assistant for creating compelling presentations and proposals.

## Setup

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)

### Installation

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and setup the project**:
   ```bash
   git clone <your-repo-url>
   cd PitchBot
   ```

3. **Create virtual environment and install dependencies**:
   ```bash
   uv venv --python 3.12
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

4. **Install development dependencies** (optional):
   ```bash
   uv pip install -e ".[dev]"
   ```

### Environment Variables

Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_api_key
LLAMA_API_KEY=your_llama_api_key
```

### Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
python -m pitchbot
```

## AI Website Scraper

The AI Website Scraper is a comprehensive web scraping solution that combines intelligent content analysis with Llama 4 API integration. It uses a hybrid approach combining sitemap parsing, content-aware filtering, strategic crawling, and limited recursive discovery.

### Features

- **Intelligent Content Scoring**: Prioritizes high-value pages based on URL patterns and content analysis
- **Sitemap Discovery & Parsing**: Automatically finds and parses XML sitemaps
- **Robots.txt Compliance**: Respects website crawling policies
- **Rate Limiting & Politeness**: Configurable delays and concurrent request limits
- **Llama 4 Integration**: Uses Llama API for content summarization and key point extraction
- **Error Handling & Resilience**: Comprehensive error handling with retry logic
- **Caching System**: Avoids duplicate work with intelligent caching
- **Batch Processing**: Process multiple websites efficiently

### Command Line Usage

```bash
# Basic scraping
python scrape_website.py https://example.com

# Custom configuration
python scrape_website.py https://example.com --max-pages 50 --output results.json

# Polite crawling with delays
python scrape_website.py https://example.com --delay 2.0 --concurrent 3

# High-quality content only
python scrape_website.py https://example.com --content-threshold 0.6

# Verbose logging
python scrape_website.py https://example.com --verbose

# Dry run (show configuration without scraping)
python scrape_website.py https://example.com --dry-run
```

### Python API Usage

```python
from pitchbot import RobustWebsiteScraper, scrape_website

# Quick scraping with convenience function
results = await scrape_website(
    base_url="https://example.com",
    max_pages=100,
    output_path="results.json"
)

# Advanced configuration
scraper = RobustWebsiteScraper(
    base_url="https://example.com",
    max_pages=500,
    max_depth=5,
    delay=1.0,
    concurrent_requests=5,
    content_threshold=0.4,
    cache_duration=3600,
    llama_model="Llama-4-Maverick-17B-128E-Instruct-FP8"
)

results = await scraper.scrape_comprehensive()
scraper.save_results("detailed_results.json")

# Analyze results
summary = scraper.get_results_summary()
print(f"Scraped {summary['scraping_session']['total_pages']} pages")
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | Required | Starting URL for scraping |
| `max_pages` | 1000 | Maximum pages to process |
| `max_depth` | 5 | Maximum crawl depth |
| `delay` | 1.0 | Delay between requests (seconds) |
| `concurrent_requests` | 5 | Maximum concurrent requests |
| `content_threshold` | 0.4 | Minimum content score to process (0.0-1.0) |
| `cache_duration` | 3600 | Cache duration in seconds |
| `llama_model` | Llama-4-Maverick-17B-128E-Instruct-FP8 | Llama model for content analysis |

### Content Scoring

The scraper uses intelligent content scoring to prioritize high-value pages:

**High-Value Patterns** (positive scoring):
- `/how-it-works/`, `/pricing/`, `/use-cases/`, `/help/`
- `/blog/`, `/articles/`, `/docs/`, `/features/`
- `/solutions/`, `/guides/`, `/tutorials/`, `/documentation/`

**Low-Value Patterns** (negative scoring):
- `/contact/`, `/privacy/`, `/terms/`, `/login/`
- `/cart/`, `/search/`, `/sitemap/`
- Static files: `.css`, `.js`, `.pdf`, `.jpg`, etc.

### Output Format

Results are saved in JSON format with the following structure:

```json
{
  "scraping_session": {
    "start_time": "2025-01-21T10:00:00Z",
    "end_time": "2025-01-21T10:30:00Z",
    "base_url": "https://example.com",
    "total_pages": 150,
    "successful_pages": 120,
    "failed_pages": 30,
    "total_time": 1800.5,
    "configuration": {...}
  },
  "results": [
    {
      "url": "https://example.com/article1",
      "title": "Article Title",
      "summary": "AI-generated summary...",
      "key_points": ["Point 1", "Point 2"],
      "content_score": 0.85,
      "word_count": 1200,
      "processing_time": 2.3,
      "error": null
    }
  ]
}
```

### Examples

Run the comprehensive examples:

```bash
python examples/website_scraper_example.py
```

## PDF Ingestion & Processing

The PDF ingest component extracts text from PDFs locally and processes it using Llama API.

### Usage
```python
from pitchbot import PDFIngest

# Full processing (extraction + Llama processing)
ingest = PDFIngest()
result = ingest.process_pdf("public/example_document.pdf")
print(result["summary"])        # Llama-generated summary
print(result["key_points"])     # Extracted key points
print(result["raw_text"])       # Original extracted text

# Local extraction only
raw_result = ingest.extract_only("public/example_document.pdf")
print(raw_result["text"])       # Just the extracted text

# Quick summary
summary = ingest.summarize_pdf("public/example_document.pdf")

# Comprehensive insights
insights = ingest.get_pdf_insights("public/example_document.pdf")

# Answer specific questions
questions = ["What is the target market?", "What are the revenue projections?"]
answers = ingest.answer_questions("public/example_document.pdf", questions)

# Custom processing
custom_result = ingest.process_custom("public/example_document.pdf", "Analyze this from a business perspective")
```

### Features

- **Multiple PDF Libraries**: Uses PyMuPDF, pdfplumber, pdfminer, and PyPDF2 with intelligent fallback
- **Text Extraction**: Extracts text while preserving structure and formatting
- **Table Extraction**: Extracts tables as structured data using pdfplumber
- **Metadata Extraction**: Extracts document metadata (title, author, pages, dates)
- **Llama Integration**: Processes extracted text using Llama API for:
  - Summarization (executive, detailed, bullet points)
  - Key point extraction
  - Question answering
  - Custom analysis
- **Smart Chunking**: Handles large documents by chunking text for token limits
- **Error Handling**: Graceful fallback if Llama API fails
- **Batch Processing**: Process multiple PDFs efficiently

### Examples

Run the examples to see the PDF ingestion component in action:

```bash
python examples/pdf_ingest_examples.py
```

## Testing

Run comprehensive tests for all components:

```bash
# Run all tests
pytest

# Run specific test files
pytest tests/test_website_scraper.py -v
pytest tests/test_pdf_ingest.py -v

# Run with coverage
pytest --cov=pitchbot --cov-report=html
```

## Development

- **Code formatting**: `black .`
- **Import sorting**: `isort .`
- **Type checking**: `mypy .`
- **Testing**: `pytest`

## Architecture

The project follows a modular architecture:

```
pitchbot/
├── main.py                 # Main entry point
├── website_scraper.py      # AI Website Scraper
├── pdf_ingest/            # PDF processing components
│   ├── ingest.py          # Main orchestrator
│   ├── pdf_processor.py   # PDF extraction
│   ├── text_processor.py  # Llama API integration
│   └── html_processor.py  # HTML processing
└── tests/                 # Comprehensive test suite
```

## Security & Ethics

- **Robots.txt Compliance**: Always respects website crawling policies
- **Rate Limiting**: Configurable delays to be respectful to servers
- **User-Agent Identification**: Proper identification in requests
- **Error Handling**: Graceful degradation when APIs are unavailable
- **GDPR Compliance**: Implements content filtering for sensitive material
