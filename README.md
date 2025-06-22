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

## PDF Ingestion & Processing

The PDF ingest component extracts text from PDFs locally and processes it using Llama API.

### Usage
```python
from pitchbot import PDFIngest

# Full processing (extraction + Llama processing)
ingest = PDFIngest()
result = ingest.process_pdf("document.pdf")
print(result["summary"])        # Llama-generated summary
print(result["key_points"])     # Extracted key points
print(result["raw_text"])       # Original extracted text

# Local extraction only
raw_result = ingest.extract_only("document.pdf")
print(raw_result["text"])       # Just the extracted text

# Quick summary
summary = ingest.summarize_pdf("document.pdf")

# Comprehensive insights
insights = ingest.get_pdf_insights("document.pdf")

# Answer specific questions
questions = ["What is the main topic?", "What are the key findings?"]
answers = ingest.answer_questions("document.pdf", questions)

# Custom processing
custom_result = ingest.process_custom("document.pdf", "Analyze this from a business perspective")
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

## Development

- **Code formatting**: `black .`
- **Import sorting**: `isort .`
- **Type checking**: `mypy .`
- **Testing**: `pytest`
