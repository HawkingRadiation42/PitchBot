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
BRAVE_API_KEY=your_brave_search_api_key
```

**Note**: The BRAVE_API_KEY is required for the agentic search functionality that performs market research. You can get a free API key from [Brave Search API](https://api.search.brave.com/).

### Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
python -m pitchbot
```

## Development

- **Code formatting**: `black .`
- **Import sorting**: `isort .`
- **Type checking**: `mypy .`
- **Testing**: `pytest`
