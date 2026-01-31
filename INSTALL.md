# Installation & Setup Guide

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- API key for either:
  - Anthropic (Claude)
  - OpenAI (GPT-4)

## Step-by-Step Installation

### 1. Install Python Dependencies

```bash
# Navigate to project directory
cd medical-paper-summarizer

# Install all required packages
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Add your API keys to `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### 3. Download NLTK Data (Optional but Recommended)

For better sentence segmentation:

```bash
python -c "import nltk; nltk.download('punkt')"
```

### 4. Verify Installation

```bash
# Run tests
pytest tests/ -v

# Run examples
python examples.py
```

## Quick Test

Create a simple test script:

```python
from summarization.summarizer import MedicalPaperSummarizer

summarizer = MedicalPaperSummarizer()
print("✓ Installation successful!")
print(f"Using model: {summarizer.llm.primary_model}")
```

## Common Issues

### ImportError: No module named 'anthropic'

```bash
pip install anthropic
```

### ImportError: No module named 'pdfplumber'

```bash
pip install pdfplumber
```

### API Key Not Found

Make sure `.env` file is in the project root directory and contains:

```
ANTHROPIC_API_KEY=your_actual_key_here
```

### PDF Extraction Issues

If PDF extraction fails:

1. Try using PyMuPDF instead:
   ```python
   loader = PDFLoader(use_pymupdf=True)
   ```

2. Check if PDF is text-based (not scanned):
   - Use `pdftotext` command line tool to test
   - If scanned, use OCR first (pytesseract)

### Memory Issues with Large Papers

Reduce chunk size:

```python
summarizer = MedicalPaperSummarizer(
    chunk_size=800,  # Smaller chunks
    chunk_overlap=150
)
```

## Optional: Virtual Environment

Recommended for isolation:

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Development Setup

For contributors:

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black mypy

# Set up pre-commit hooks (optional)
black medical-paper-summarizer/
mypy medical-paper-summarizer/
```

## Next Steps

1. Try the CLI: `python app.py --help`
2. Run examples: `python examples.py`
3. Process a test paper: `python app.py path/to/paper.pdf`
4. Read the full documentation: See README.md

## Support

For issues:
1. Check troubleshooting section in README.md
2. Verify API keys are valid
3. Check Python version (3.10+)
4. Review error messages carefully
5. Open GitHub issue if problem persists
